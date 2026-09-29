param(
    [ValidateSet("jsonrpc", "http_json", "all")]
    [string]$Transport = "all",

    [ValidateSet("must", "should", "may", "all")]
    [string]$Level = "all",

    [string]$TckRevision = "main",

    [string]$HostAddress = "127.0.0.1",

    [int]$Port = 41241,

    [string[]]$PytestArgs = @()
)

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$repositoryPython = Join-Path $repositoryRoot "venv\Scripts\python.exe"
$agentPath = Join-Path $PSScriptRoot "agent.py"
$tckPath = Join-Path $PSScriptRoot ".tck"
$tckPython = Join-Path $tckPath ".venv\Scripts\python.exe"
$stdoutLog = Join-Path $PSScriptRoot "agent.stdout.log"
$stderrLog = Join-Path $PSScriptRoot "agent.stderr.log"
$sutHost = "http://${HostAddress}:$Port/rpc"

if (-not (Test-Path $repositoryPython)) {
    throw "Repository virtual environment not found. Run .\scripts\dev_setup.ps1 first."
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git was not found on PATH."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found on PATH. Install it from https://docs.astral.sh/uv/."
}

if (-not (Test-Path (Join-Path $tckPath ".git"))) {
    git clone https://github.com/a2aproject/a2a-tck.git $tckPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to clone the A2A TCK repository."
    }
}

git -C $tckPath fetch origin $TckRevision
if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch TCK revision '$TckRevision'."
}

git -C $tckPath checkout --detach FETCH_HEAD
if ($LASTEXITCODE -ne 0) {
    throw "Failed to check out TCK revision '$TckRevision'."
}

if (-not (Test-Path $tckPython)) {
    uv venv (Join-Path $tckPath ".venv") --python 3.11
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the TCK virtual environment."
    }
}

& $tckPython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) {
    throw "Failed to bootstrap pip in the TCK virtual environment."
}

& $tckPython -m pip install -e $tckPath
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install the TCK."
}

Remove-Item $stdoutLog, $stderrLog -ErrorAction SilentlyContinue

$agentProcess = $null
$exitCode = 1

try {
    $agentProcess = Start-Process `
        -FilePath $repositoryPython `
        -ArgumentList @($agentPath, "--host", $HostAddress, "--port", $Port) `
        -WorkingDirectory $repositoryRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru

    $healthUrl = "http://${HostAddress}:$Port/health"
    $deadline = (Get-Date).AddSeconds(30)
    $healthy = $false

    while ((Get-Date) -lt $deadline) {
        if ($agentProcess.HasExited) {
            break
        }

        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }

    if (-not $healthy) {
        if (Test-Path $stderrLog) {
            Get-Content $stderrLog
        }
        throw "The A2A test agent did not become healthy at $healthUrl."
    }

    $tckArguments = @(
        (Join-Path $tckPath "run_tck.py"),
        "--sut-host",
        $sutHost,
        "-v"
    )

    if ($Transport -eq "all") {
        $tckArguments += @("--transport", "jsonrpc,http_json")
    }
    else {
        $tckArguments += @("--transport", $Transport)
    }

    if ($Level -ne "all") {
        $tckArguments += @("--level", $Level)
    }

    if ($PytestArgs.Count -gt 0) {
        $tckArguments += "--"
        $tckArguments += $PytestArgs
    }

    Push-Location $tckPath
    try {
        & $tckPython @tckArguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($null -ne $agentProcess -and -not $agentProcess.HasExited) {
        Stop-Process -Id $agentProcess.Id
        $agentProcess.WaitForExit()
    }
}

exit $exitCode

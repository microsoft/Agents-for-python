<#
.SYNOPSIS
    Run the python-sdk-tests suite in Docker.

.DESCRIPTION
    1. Verifies that .env exists (fail-fast if azd provision hasn't run).
    2. Builds tests.Dockerfile (tagged agents-test).
    3. Runs pytest inside the container with the repo mounted at /repo.

    Run `azd up` from this directory first to provision Azure resources and
    populate .env via the postprovision hook.

    Run from anywhere — the script resolves all paths from its own location.

.EXAMPLE
    # Run tests (azd up already completed):
    ./scripts/run_local.ps1

    # Skip Docker build (reuse existing image):
    ./scripts/run_local.ps1 -NoBuild

.PARAMETER TestPath
    pytest path to run inside the container. Default: tests/

.PARAMETER NoBuild
    Skip the docker build step (reuse the existing agents-test image).
#>
param(
    [string]$TestPath = "tests/",

    [switch]$NoBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$EnvDir  = (Resolve-Path "$PSScriptRoot/..").Path
$RepoRoot = (Resolve-Path "$PSScriptRoot/..").Path

Push-Location $RepoRoot
try {
    # ------------------------------------------------------------------ #
    # 1. Pre-flight: verify .env exists                                   #
    # ------------------------------------------------------------------ #
    if (-not (Test-Path "$EnvDir/.env")) {
        Write-Error (
            ".env not found. Run 'azd up' from this directory first to " +
            "provision Azure resources and populate .env via the postprovision hook."
        )
        exit 1
    }

    # ------------------------------------------------------------------ #
    # 2. Build Docker image                                               #
    # ------------------------------------------------------------------ #
    if (-not $NoBuild) {
        Write-Host "Building agents-test image..."
        docker build -f tests.Dockerfile -t agents-test .
    }

    # ------------------------------------------------------------------ #
    # 3. Run tests                                                        #
    # ------------------------------------------------------------------ #
    Write-Host "Running tests: $TestPath"
    docker run --rm `
        -v "${RepoRoot}:/repo" `
        agents-test `
        $TestPath

} finally {
    Pop-Location
}

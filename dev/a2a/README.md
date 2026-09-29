# A2A TCK development harness

This directory contains a local A2A agent and a PowerShell runner for the
official [A2A Technology Compatibility Kit][tck].

## Prerequisites

From the repository root, prepare the development environment:

```powershell
.\scripts\dev_setup.ps1
```

Install [uv](https://docs.astral.sh/uv/) and ensure `git` is available on
`PATH`.

## Run the TCK

From the repository root:

```powershell
.\dev\a2a\run_tck.ps1
```

The script:

1. Clones or updates the TCK under `dev\a2a\.tck`.
2. Creates the TCK virtual environment and installs its dependencies.
3. Starts the local agent on `http://127.0.0.1:41241`.
4. Runs the TCK against the JSON-RPC and HTTP+JSON interfaces.
5. Stops the local agent.

By default, the complete suite runs for both supported transports. Examples:

```powershell
# Run only MUST requirements over JSON-RPC.
.\dev\a2a\run_tck.ps1 -Transport jsonrpc -Level must

# Run only HTTP+JSON against a specific TCK revision.
.\dev\a2a\run_tck.ps1 -Transport http_json -TckRevision main

# Forward additional arguments to pytest through the TCK.
.\dev\a2a\run_tck.ps1 -PytestArgs "-x", "--pdb"
```

TCK reports are written under `dev\a2a\.tck\reports`.

The test agent intentionally disables JWT authentication. It is only intended
for local protocol compatibility testing.

[tck]: https://github.com/a2aproject/a2a-tck


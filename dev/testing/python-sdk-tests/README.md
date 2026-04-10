# Python SDK Integration Tests

Integration tests for the Python SDK. Unlike `cross-sdk-tests`, these tests run agents in-process and have access to SDK internals (state, routing, middleware) via the `microsoft-agents-testing` framework.

## Directory Structure

```
tests/
  integration/       # Tests against locally-running agents
    dialogs/         # Dialog-specific integration tests
    test_quickstart.py
    test_expect_replies.py
    test_streaming_response.py
    test_telemetry.py
  scenarios/         # Agent definitions used by the tests
    quickstart.py
tests.Dockerfile     # Dockerfile for running tests in CI
scripts/             # Provisioning and environment scripts
```

## Setup

**Prerequisites**: Python 3.13+, [uv](https://docs.astral.sh/uv/)

### Option 1 — Manual

Copy `.env` from the template and fill in your app credentials:

```bash
cp env.TEMPLATE .env
```

| Variable | Description |
|----------|-------------|
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID` | Azure app client ID |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID` | Azure tenant ID |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET` | Azure client secret |

### Option 2 — azd (recommended)

`azd up` provisions the required Azure resources (App Registration, Azure Bot, Key Vault) and the postprovision hook automatically populates `.env`:

```bash
azd env new e2e-python
azd up
```

To tear down:

```bash
azd down
```

### Install dependencies

```bash
uv sync
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run a specific file
uv run pytest tests/integration/test_quickstart.py

# Run with verbose output
uv run pytest -v
```

### Docker (via run_local.ps1)

To run tests inside a Docker container (requires `azd up` to have been run first):

```powershell
./scripts/run_local.ps1

# Skip Docker build (reuse existing image):
./scripts/run_local.ps1 -NoBuild
```

## Writing Tests

See [microsoft-agents-testing/README.md](../microsoft-agents-testing/README.md) for full framework documentation.

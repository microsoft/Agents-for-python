## Testing

This folder contains two test-related directories:

`microsoft-agents-testing`: The testing framework used to facilitate testing agents. Handles auth, in-process agent hosting, activity construction, and response collection. Internal use only.

`python-sdk-tests`: Integration tests for the Python SDK. These run agents in-process and have access to SDK internals (state, routing, middleware), making them more targeted than HTTP-level end-to-end tests.

## Running Tests

### Option 1 — Local (manual setup)

Manually populate `.env` with credentials, then run uv run pytest directly:

```bash
cd python-sdk-tests
cp env.TEMPLATE .env  # fill in credentials
uv sync
uv run pytest
```

### Option 2 — azd (recommended)

Use `azd` to provision the required Azure resources (App Registration, Azure Bot, Key Vault) and automatically populate `.env` via the postprovision hook:

```bash
cd python-sdk-tests
azd env new e2e-python
azd up   # provisions infra and runs postprovision hook to write .env
uv run pytest
```

To tear down the Azure resources:

```bash
azd down
```

### Option 3 — Docker (via run_local.ps1)

Builds and runs tests inside a Docker container. Requires `azd up` to have been run first:

```powershell
./scripts/run_local.ps1

# Skip Docker build (reuse existing image):
./scripts/run_local.ps1 -NoBuild
```

See [python-sdk-tests/README.md](python-sdk-tests/README.md) for more details.

### microsoft-agents-testing

This is a library, not a test suite. Installation instructions are in [microsoft-agents-testing/README.md](microsoft-agents-testing/README.md).

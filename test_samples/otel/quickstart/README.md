# OpenTelemetry quickstart sample

This sample configures OpenTelemetry providers and library instrumentation in
application code. See `../zero-code` for the equivalent agent using
OpenTelemetry auto-instrumentation and environment configuration.

## Set up

From this directory, create the project environment and copy the configuration
template:

```powershell
uv sync
Copy-Item env.TEMPLATE .env
```

`uv sync` installs the Microsoft Agents packages in editable mode from this
repository's `libraries/` directory, so local SDK changes are immediately
available to the sample. Set the agent registration and OAuth connection values
in `.env`.

## Run

Start the local Aspire dashboard:

```powershell
.\start_dashboard.ps1
```

In another terminal, start the agent:

```powershell
uv run python -m src.main
```

Open the dashboard at <http://localhost:18888>. The agent listens at
<http://localhost:3978/api/messages>.

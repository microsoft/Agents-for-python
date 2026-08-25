# Zero-code OpenTelemetry sample

This sample has the same agent behavior as `../quickstart`, but it does not
configure OpenTelemetry in the application. The OpenTelemetry Python distro
discovers and instruments installed libraries, while environment variables
configure the SDK and OTLP exporters before the application is imported.

## Set up

From this directory, install the project and copy the configuration template:

```powershell
uv sync
Copy-Item env.TEMPLATE .env
```

`uv sync` creates the virtual environment, installs the agent and OpenTelemetry
dependencies, and registers `src.typing_sampler` as an OpenTelemetry sampler
entry point. The Microsoft Agents packages are installed in editable mode from
this repository's `libraries/` directory, so local SDK changes are picked up
without publishing packages. Set the agent registration and OAuth connection
values in `.env`.

## Run

Start the local Aspire dashboard:

```powershell
.\start_dashboard.ps1
```

In another terminal, start the agent:

```powershell
.\start_agent.ps1
```

`uv run --env-file .env` loads the configuration before starting
`opentelemetry-instrument`. Loading the environment first is important because
the OpenTelemetry distro reads its configuration and installs instrumentation
before `src.main` is imported.

`OTEL_TRACES_SAMPLER=drop_typing` selects the sampler plugin. It drops the
`agents.app.send_typing` span. OpenTelemetry gives its descendants the resulting
unsampled parent context, so the sampler drops those spans too. Other traces use
parent-based always-on sampling.

Open the dashboard at <http://localhost:18888>. The agent listens at
<http://localhost:3978/api/messages>.

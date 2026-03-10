# Weather Agent Sample

A sample agent built with the Microsoft 365 Agents SDK for Python. It uses Azure OpenAI for natural language understanding, OpenWeatherMap for weather lookups, and exports telemetry to an Aspire dashboard via OpenTelemetry.

## Prerequisites

- **Python 3.11+** (3.10+ supported)
- **Docker** (for the Aspire observability dashboard)
- **Azure OpenAI** deployment
- **OpenWeatherMap API key** — get a free key at <https://openweathermap.org/price>
- **Azure AD app registration** (for M365/Teams auth) — or use the default dev values

## 1. Start the Aspire Dashboard

The sample exports traces, metrics, and logs via OTLP. Run the Aspire dashboard container so there is a collector listening:

```bash
docker run --rm -it -p 18888:18888 -p 4317:18889 \
  --name aspire-dashboard \
  mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

Once running, open **http://localhost:18888** in your browser to view telemetry.

> The agent sends OTLP data to `localhost:4317`, which the container maps to its internal port `18889`.

## 2. Create a Virtual Environment & Install Dependencies

From the repository root:

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

Then install the SDK libraries in editable mode (if not already):

```bash
pip install -e ./libraries/microsoft-agents-activity/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat
```

Install the sample's own dependencies:

```bash
pip install -r test_samples/weather-agent-framework/requirements.txt
```

## 3. Configure the `.env` File

Copy the example and fill in your values:

```bash
cp test_samples/weather-agent-framework/.env.example test_samples/weather-agent-framework/.env
```

Open the `.env` file and set the following variables:

### M365 Agents SDK / Azure AD

| Variable | Where to get it |
|---|---|
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID` | Azure Portal → **App registrations** → your app → **Application (client) ID** |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET` | Azure Portal → **App registrations** → your app → **Certificates & secrets** → create a new client secret |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID` | Azure Portal → **App registrations** → your app → **Directory (tenant) ID** |

> For local development without Teams/M365 auth you can leave these as the placeholder values.

### Azure OpenAI

| Variable | Where to get it |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure Portal → **Azure OpenAI** resource → **Keys and Endpoint** → copy the endpoint URL |
| `AZURE_OPENAI_API_KEY` | Same page → copy **Key 1** or **Key 2** |
| `AZURE_OPENAI_DEPLOYMENT` | Azure Portal → **Azure OpenAI** → **Model deployments** → the deployment name (e.g. `gpt-4o-mini`) |
| `AZURE_OPENAI_API_VERSION` | Use `2024-12-01-preview` or a later supported version |

### OpenWeatherMap

| Variable | Where to get it |
|---|---|
| `OPENWEATHER_API_KEY` | <https://openweathermap.org/price> → sign up for a free account, then copy the API key from your account page |

### Observability (pre-configured defaults)

The remaining variables in `.env.example` point to the local Aspire dashboard and enable OpenTelemetry export. The defaults work out of the box when the Docker container from Step 1 is running. No changes needed unless you want to send telemetry elsewhere (e.g. Azure Monitor via `APPLICATIONINSIGHTS_CONNECTION_STRING`).

## 4. Run the Agent

```bash
cd test_samples/weather-agent-framework
python app.py
```

The agent starts at **http://localhost:3978/api/messages**.

## 5. Test the Agent

Use [M365 Agents Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit) or a Teams channel pointed at a dev tunnel:

```bash
# Dev tunnel setup (optional, for Teams testing)
devtunnel user login
devtunnel create my-tunnel -a
devtunnel port create -p 3978 my-tunnel
devtunnel host -a my-tunnel
```

Example queries:
- *"What's the weather in Seattle, Washington?"*
- *"What's the forecast for New York, New York?"*
- *"What's the current date and time?"*

## Project Structure

```
weather-agent-framework/
├── app.py                       # aiohttp entry point
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
├── agents/
│   ├── __init__.py
│   └── weather_agent.py         # Agent logic (Azure OpenAI + tool calls)
├── tools/
│   ├── __init__.py
│   ├── weather_tools.py         # Current weather & 5-day forecast
│   └── datetime_tools.py        # Current date/time helper
└── telemetry/
    ├── __init__.py
    ├── agent_otel_extensions.py # OTel setup helpers
    ├── agent_metrics.py         # Custom metrics
    └── a365_otel_wrapper.py     # A365 observability wrapper
```

## Further Reading

- [Microsoft 365 Agents SDK Documentation](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [.NET Aspire Dashboard](https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/dashboard/standalone)

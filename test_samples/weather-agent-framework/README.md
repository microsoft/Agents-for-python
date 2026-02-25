# Overview

This sample demonstrates how to build an agent using the Microsoft 365 Agents SDK for Python that:
- Hosts an agent using `agent-framework` or `microsoft-agents-hosting-aiohttp`
- Integrates Azure OpenAI for natural language understanding
- Implements weather lookup tools using OpenWeatherMap API
- Supports streaming responses

## Project Structure

```
python-agent/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── app.py                 # M365 Agents SDK with aiohttp
├── agent/
│   ├── __init__.py
│   └── weather_agent.py        # Weather agent class (M365 SDK version)
└── tools/
    ├── __init__.py
    ├── weather_tools.py        # Weather lookup tools
    └── datetime_tools.py       # DateTime helper tools
```

## Prerequisites

- Python 3.11 or later (3.10+ supported, 3.11+ recommended for optimal performance)
- Azure OpenAI deployment
- OpenWeatherMap API key (free tier available at https://openweathermap.org/)

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the `.env.example` to `.env` and configure:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# OpenWeatherMap API Key
OPENWEATHER_API_KEY=your-openweather-api-key

# Server Configuration (optional)
PORT=3978
HOST=localhost
```

2. For production, use Azure Key Vault or environment variables instead of `.env` file.

## Running the Agent

For Teams/M365 integration with web endpoint:

```bash
python app.py
```

The agent will be available at `http://localhost:3978/api/messages`

Test with Agent Playground or Teams:
- Ensure Agent Playground is installed
- Configure the endpoint in your agent manifest
- Test through Agent Playground or Teams interface

## Tools Implemented

1. **Weather Lookup Tools** (`tools/weather_tools.py`)
   - `get_current_weather_for_location(location, state)` - Current weather conditions
   - `get_weather_forecast_for_location(location, state)` - 5-day forecast

2. **DateTime Tools** (`tools/datetime_tools.py`)
   - `get_date_time()` - Current date and time

## Testing

Test the agent with queries like:
- "What's the weather in Seattle, Washington?"
- "What's the forecast for New York, New York?"
- "What's the current date and time?"


## Further Reading

- [Microsoft 365 Agents SDK Documentation](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/)
- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [OpenWeatherMap API](https://openweathermap.org/api)

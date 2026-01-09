# 🤖 Agents SDK Test Framework's Python Bot

This Python bot is part of the Agents SDK Test Framework. It exercises agent behaviors, validates responses, and helps iterate on integrations with LLMs and tools.

## Highlights ✨
- ⚙️ Test-runner for validating agent flows and tool/function calling
- 🧠 Integrates with LLM providers (Azure OpenAI, Semantic Kernel)
- 🖥️ Uses Microsoft Agents SDK packages for hosting and activity management

## 🚀 Getting Started

### 🛠️ Prerequisites
- Python 3.9+
- `pip` (Python package manager)

### 📦 Installation
1. Install dependencies:
   ```powershell
   pip install --pre --no-deps -r pre_requirements.txt
   pip install -r requirements.txt
   ```
#### ℹ️ Why are there two installation steps?

**Dependency installation is split into two steps to ensure reliability and avoid conflicts:**

- **Step 1:** `pre_requirements.txt` — Installs core Microsoft Agents SDK packages. These may require pre-release flags or special handling, and installing them first (without dependency resolution) helps prevent version clashes.
- **Step 2:** `requirements.txt` — Installs the rest of the project dependencies, after the core packages are in place, to ensure compatibility and a smooth setup.

This approach helps avoid dependency issues and guarantees all required packages are installed in the correct order.

### ⚙️ Set up Environment Variables
Copy or rename `.envLocal` to `.env` and fill in the required values (keys, endpoints, etc.).

> 💡 Tip: The repo often uses Azure resources (Azure OpenAI / Bot Service) in examples.

### ▶️ Running the Agent
Start the agent locally:
```powershell
python app.py
```

## 📁 Project Layout
```
Agent/python/
    agent.py
    app.py
    config.py
    requirements.txt
    requirements2.txt
    pre_requirements.txt
    .env
    .envLocal
    weather/
        agents/
            weather_forecast_agent.py
            weather_forecast_agent_response.py
        plugins/
            adaptive_card_plugin.py
            date_time_plugin.py
            weather_forecast_plugin.py
            weather_forecast.py
```

This launches the process that hosts the agent and exposes the `/api/messages` endpoint.

## 📚 Key Dependencies
- `microsoft-agents-hosting-core`, `microsoft-agents-hosting-aiohttp`, `microsoft-agents-activity`, `microsoft-agents-authentication-msal` — Microsoft Agents SDK packages
- `semantic-kernel` — LLM orchestration
- `openai` — Azure OpenAI integration

## Health & Messaging Endpoints
- Health check: (if exposed) `GET /` should return 200
- Messaging / activity endpoint: `POST /api/messages` (see `app.py`)

## Agent Flow 🔁
1. The test runner accepts scenario inputs (natural language user messages).
2. It forwards activity payloads to the agent runtime.
3. The agent may call functions/tools (e.g., weather, date/time).
4. The runner validates the agent's JSON / Adaptive Card outputs and records results.

## Contributing
- Open a PR with changes and add a short description of the test scenarios you added or modified.

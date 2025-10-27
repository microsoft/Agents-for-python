# Microsoft Agents Hosting FastAPI

This library provides FastAPI integration for Microsoft Agents, enabling you to build conversational agents using the FastAPI web framework.

## Features

- FastAPI integration for Microsoft Agents
- JWT authorization middleware
- Channel service API endpoints
- Streaming response support
- Cloud adapter for processing agent activities

## Installation

```bash
pip install microsoft-agents-hosting-fastapi
```

## Usage

```python
from fastapi import FastAPI, Request
from microsoft_agents.hosting.fastapi import start_agent_process, CloudAdapter
from microsoft_agents.hosting.core.app import AgentApplication

app = FastAPI()
adapter = CloudAdapter()
agent_app = AgentApplication()

@app.post("/api/messages")
async def messages(request: Request):
    return await start_agent_process(request, agent_app, adapter)
```
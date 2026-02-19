# Microsoft Agents Hosting FastAPI

This library provides FastAPI integration for Microsoft Agents, enabling you to build conversational agents using the FastAPI web framework.

## Release Notes
<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>0.7.0</td>
    <td>2026-01-21</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v070">
        0.7.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>0.6.1</td>
    <td>2025-12-01</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v061">
        0.6.1 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>0.6.0</td>
    <td>2025-11-18</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v060">
        0.6.0 Release Notes
      </a>
    </td>
  </tr>
</table>

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
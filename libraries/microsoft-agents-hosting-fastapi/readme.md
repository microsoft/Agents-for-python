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
    <td>1.3.0</td>
    <td>2026-07-30</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v130">
        1.3.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.2.0</td>
    <td>2026-07-17</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v120">
        1.2.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.1.0</td>
    <td>2026-06-19</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v110">
        1.1.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.0.0</td>
    <td>2026-05-22</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v100">
        1.0.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>0.9.1</td>
    <td>2026-05-04</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v091">
        0.9.1 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>0.9.0</td>
    <td>2026-04-15</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v090">
        0.9.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>0.8.0</td>
    <td>2026-02-23</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v080">
        0.8.0 Release Notes
      </a>
    </td>
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

## Packages Overview

We offer the following PyPI packages to create conversational experiences based on Agents:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-activity` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/) | Types and validators implementing the Activity protocol spec. |
| `microsoft-agents-hosting-core` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/) | Core library for Microsoft Agents hosting. |
| `microsoft-agents-hosting-aiohttp` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/) | Configures aiohttp to run the Agent. |
| `microsoft-agents-hosting-fastapi` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-fastapi)](https://pypi.org/project/microsoft-agents-hosting-fastapi/) | Configures fastapi to run the Agent. |
| `microsoft-agents-hosting-msteams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-hosting-dialogs` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/) | Dialog system with waterfall dialogs, prompts, and multi-turn conversation management. |
| `microsoft-agents-hosting-slack` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/) | Provides classes to host an Agent for Slack. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |
| `microsoft-agents-authentication-entra-auth-sidecar` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-entra-auth-sidecar)](https://pypi.org/project/microsoft-agents-authentication-entra-auth-sidecar/) | Credential-free Entra ID Agent ID authentication via the sidecar. | 

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
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)
agent_app = AgentApplication()

@app.post("/api/messages")
async def messages(request: Request):
    return await start_agent_process(request, agent_app, adapter)
```
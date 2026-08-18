# Microsoft Agents Hosting - Slack

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/)

Integration library for building Slack agents using the Microsoft 365 Agents SDK. Provides direct-to-Slack responses (the full Slack Web API surface, beyond what Azure Bot Service exposes), a typed `SlackChannelData` envelope with dot-notation property access, and a `SlackStream` helper for `chat.startStream` / `chat.appendStream` / `chat.stopStream`.


## Release Notes

<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
   <td>1.4.0</td>
   <td>2026-08-18</td>
   <td>
     <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v140">
       1.4.0 Release Notes
     </a>
   </td>
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

## Installation

```bash
pip install microsoft-agents-hosting-slack
```

## Usage

```python
from microsoft_agents.hosting.core.app import AgentApplication
from microsoft_agents.hosting.slack import SlackAgentExtension
from microsoft_agents.hosting.slack.api import SlackChannelData

app = AgentApplication(options)
slack = SlackAgentExtension(app)

@slack.on_message()
async def on_slack_message(context, state):
    channel_data = SlackChannelData.from_activity(context.activity)
    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.get("event.channel"),
            "text": f"You said: {context.activity.text}",
        },
        token=channel_data.api_token,
    )
```

## Key Classes

- **`SlackAgentExtension`** — registers Slack-channel-scoped message/event handlers; exposes `call(...)` and `create_stream(...)`.
- **`SlackChannelData`** — typed wrapper around Bot Service's Slack channel-data payload with `get(path)` / `try_get(path)` accessors.
- **`SlackApi`** — async HTTP client for the Slack Web API.
- **`SlackStream`** — wraps Slack's streaming methods for incremental message updates.
- **`SlackHelpers`** — encode/decode and conversation-id parsing utilities.

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

# Microsoft Agents Hosting - Slack

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/)

Build Slack agents with the Microsoft 365 Agents SDK using typed message and event
handlers, direct Slack Web API calls, and streaming responses.

## Release Notes

<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>1.9.0</td>
    <td>2026-10-19</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v190">
        1.9.0 Release Notes
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

Given configured application options (including storage) and a connection manager:

```python
from microsoft_agents.hosting.core.app import AgentApplication
from microsoft_agents.hosting.core.app.state import TurnState
from microsoft_agents.hosting.slack import SlackAgentExtension, SlackTurnContext

app = AgentApplication[TurnState](options, connection_manager=connections)
slack = SlackAgentExtension(app)

@slack.message()
async def on_slack_message(context: SlackTurnContext, state: TurnState) -> None:
    channel_data = context.activity.slack_channel_data
    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.channel,
            "text": f"You said: {context.activity.text}",
        },
        token=channel_data.api_token or "",
    )
```

Use `@slack.message("hello")` for a specific message or `@slack.event("reaction_added")`
for a specific event. Both accept a string, a compiled regular expression, or a list of
either, and match only Slack activities. When called without a selector, they match every
Slack message or event and register at `RouteRank.LAST`, so more specific routes win.
`on_message()` and `on_event()` are deprecated aliases.

`@slack.conversation_update(...)`, `@slack.members_added()`, `@slack.members_removed()`,
and `@slack.installation_update()` mirror the corresponding `AgentApplication` route
hooks, but match only Slack activities and pass a `SlackTurnContext` to the handler.

Handlers receive a `SlackTurnContext` with typed `activity.slack_channel_data` and
access to the per-turn Slack API client through `context.client`. Envelope, payload,
and response models support nested lookups such as `envelope.get("event.channel")`
and typed lookups such as `response.get("count", type_=int)`.

Use `slack.create_stream(context, thread_ts=...)` to start a `SlackStream`, then
append content and stop the stream. See the API docstrings for routing options,
client configuration, streaming requirements, and lookup behavior.

## Quick Links

- [Release Notes](https://github.com/microsoft/Agents-for-python/blob/main/changelog.md)
- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

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
    <td>1.8.0</td>
    <td>2026-10-01</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v180">
        1.8.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.7.0</td>
    <td>2026-09-17</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v170">
        1.7.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.5.0</td>
    <td>2026-08-26</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v150">
        1.5.0 Release Notes
      </a>
    </td>
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

### Routes and turn context

Use `@slack.message("hello")` for a specific message or `@slack.event("reaction_added")`
for a specific event. Both decorators match only Slack activities. String selectors
are case-sensitive exact matches; compiled regular expressions must match the entire
text or event name. Omitting the selector matches any Slack message/event and defaults
to `RouteRank.LAST`. Both decorators accept `auth_handlers` and an explicit `rank`.

Handlers receive a `SlackTurnContext` whose `activity` is a `SlackActivity`. The wrapper
shares turn state, services, and buffered replies with the original context, and
forwards the response flag and streaming-response accessor to it.

`context.client` exposes the `SlackApi` registered in turn services. Before each Slack
turn, the extension registers its shared default client only if no client is already
present. A client supplied by middleware or an earlier `before_turn` handler is
preserved, and `context.client`, `slack.call(...)`, and `slack.create_stream(...)` use
that same instance. A manually constructed context without a registered client returns
`None` from `client`. Pass `slack_api=...` to `SlackAgentExtension` to configure its
default client.

`slack.create_stream(context, thread_ts=...)` requires a Slack event envelope with
a non-empty channel ID and either an explicit thread timestamp or `event.ts`.
Missing channel or timestamp values raise `ValueError` before making an API call.

`on_message()` and `on_event()` remain available as deprecated aliases and emit
`DeprecationWarning`; new code should use `message()` and `event()`.

### Channel data and path lookups

`context.activity.slack_channel_data` exposes `envelope`, `payload`, `api_token`,
`channel`, and `thread_ts`. For a plain `TurnContext`, use
`SlackChannelData.from_activity(context.activity)`.

Path navigation belongs to the envelope, payload, and response models, not to
`SlackChannelData` itself. For example, when an envelope is present,
`channel_data.envelope.get("event.channel")` reads its channel and
`channel_data.envelope.get("event.blocks[0].type")` reads a nested array field.
Unknown Slack fields are preserved.

`get(path)` returns the value or `None` when absent; `get(path, default=...)` uses the
default only for a missing path, not for an existing null value. Supply `type_` to
convert and validate an existing value with Pydantic's `TypeAdapter`, for example
`response.get("count", type_=int)` or `response.get("event", type_=EventContent)`.
Invalid values (including null when the requested type does not accept it) raise
`pydantic.ValidationError`, even when a default is provided. Missing-path defaults
are returned unchanged, without validation. An empty path selects the entire
serialized model and applies the same validation.

Typed overloads return the requested type plus `None` when no default is supplied,
or the requested type plus the default's type when one is supplied. Without `type_`,
values remain dynamically typed. `try_get(path)` returns a raw `(found, value)`
tuple without conversion or validation.

## Key Classes

- **`SlackAgentExtension`** — registers Slack-channel-scoped `message()` / `event()` handlers; exposes `call(...)` and `create_stream(...)`.
- **`SlackTurnContext`** — Slack-aware turn context exposing the typed activity and registered API client.
- **`SlackActivity`** — activity exposing typed `slack_channel_data`.
- **`SlackChannelData`** — typed wrapper around Bot Service's Slack channel-data payload, with envelope and interactive-payload accessors.
- **`SlackModel`** — base for envelope, payload, and response models with `get(path)` / `try_get(path)` accessors.
- **`SlackApi`** — async HTTP client for the Slack Web API.
- **`SlackStream`** — wraps Slack's streaming methods for incremental message updates.
- **Helper functions** — encode/decode and conversation-id parsing utilities.

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

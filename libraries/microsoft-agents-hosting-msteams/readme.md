# microsoft-agents-hosting-msteams

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/)

Teams-specific extension for the Microsoft 365 Agents SDK for Python. Provides the `TeamsAgentExtension` and a full set of typed, decorator-based route registrars for every Teams invoke and event activity — messaging extensions, task modules, meeting lifecycle events, channel and team management, file consent, config invokes, and more.

All handlers receive a `TeamsTurnContext`, a Teams-aware wrapper around the base `TurnContext` that surfaces the Teams API client and will serve as the primary surface for Teams-specific functionality going forward.

## What is this?

This library is part of the **Microsoft 365 Agents SDK for Python** — a comprehensive framework for building enterprise-grade conversational AI agents. The SDK enables developers to create intelligent agents that work across Microsoft Teams, M365 Copilot, Copilot Studio, and web chat.

## Release Notes

<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
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
  <tr>
    <td>0.5.0</td>
    <td>2025-10-22</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v050">
        0.5.0 Release Notes
      </a>
    </td>
  </tr>
</table>

## Packages Overview

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-activity` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/) | Types and validators implementing the Activity protocol spec. |
| `microsoft-agents-hosting-core` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/) | Core library for Microsoft Agents hosting. |
| `microsoft-agents-hosting-aiohttp` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/) | Configures aiohttp to run the Agent. |
| `microsoft-agents-hosting-msteams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-hosting-dialogs` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/) | Dialog system with waterfall dialogs, prompts, and multi-turn conversation management. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |

Additionally we provide a Copilot Studio Client, to interact with Agents created in CopilotStudio:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-copilotstudio-client` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/) | Direct to Engine client to interact with Agents created in CopilotStudio |

## Installation

```bash
pip install microsoft-agents-hosting-msteams
```

## Key Classes

| Class | Description |
|-------|-------------|
| `TeamsAgentExtension` | Attaches to an `AgentApplication` and exposes all Teams route registrars as typed properties. |
| `TeamsTurnContext` | Teams-aware context passed to every handler. Provides the Teams API client and will be the primary surface for new Teams-specific capabilities. |
| `MessageExtension` | Route registrar for all `composeExtension/*` invokes (query, fetch action, submit, link unfurling, settings, etc.). |
| `TaskModule` | Route registrar for `task/fetch` and `task/submit` invokes. |
| `Meeting` | Route registrar for meeting start/end and participant join/leave events. |
| `Channel` | Route registrar for channel created/deleted/renamed/shared events. |
| `Team` | Route registrar for team archived/renamed/restored/deleted events. |
| `FileConsent` | Route registrar for file consent accept/decline invokes. |
| `Config` | Route registrar for `config/fetch` and `config/submit` invokes. |
| `Message` | Route registrar for message edit, delete, undelete, read receipts, and actionable message execute. |

## Usage

### Setup

Wrap your `AgentApplication` with `TeamsAgentExtension` to access all Teams-specific route registrars:

```python
from microsoft_agents.hosting.msteams import TeamsAgentExtension
from microsoft_agents.hosting.core import AgentApplication, TurnState

app = AgentApplication[TurnState]()
teams = TeamsAgentExtension(app)
```

Every handler receives a `TeamsTurnContext` as its first argument, giving access to the Teams API client alongside all standard `TurnContext` capabilities.

### Messaging Extensions

```python
# Search-based extension
@teams.message_extensions.query("searchCmd")
async def on_search(context: TeamsTurnContext, state, query: MessagingExtensionQuery):
    # build and return results
    return MessagingExtensionResponse(...)

# Action-based extension — open a task module to collect input
@teams.message_extensions.fetch_action("myCmd")
async def on_fetch_action(context: TeamsTurnContext, state, action: MessagingExtensionAction):
    return MessagingExtensionActionResponse(...)

# Handle submission from the task module
@teams.message_extensions.submit_action("myCmd")
async def on_submit(context: TeamsTurnContext, state, action: MessagingExtensionAction):
    return MessagingExtensionResponse(...)

# Link unfurling
@teams.message_extensions.query_link
async def on_query_link(context: TeamsTurnContext, state, query: AppBasedLinkQuery):
    return MessagingExtensionResponse(...)

# Bot message preview — edit stage
@teams.message_extensions.message_preview_edit("myCmd")
async def on_preview_edit(context: TeamsTurnContext, state, preview: Activity):
    return MessagingExtensionResponse(...)

# Bot message preview — send stage
@teams.message_extensions.message_preview_send("myCmd")
async def on_preview_send(context: TeamsTurnContext, state, preview: Activity):
    return MessagingExtensionResponse(...)
```

All `command_id` arguments accept a plain string, a compiled `re.Pattern`, or `None` to match all commands.

### Task Modules

```python
@teams.task_modules.fetch("myVerb")
async def on_task_fetch(context: TeamsTurnContext, state, request: TaskModuleRequest):
    return TaskModuleResponse(...)

@teams.task_modules.submit("myVerb")
async def on_task_submit(context: TeamsTurnContext, state, request: TaskModuleRequest):
    return TaskModuleResponse(...)
```

### Meeting Events

```python
@teams.meetings.start
async def on_meeting_start(context: TeamsTurnContext, state, meeting: MeetingDetails):
    ...

@teams.meetings.end
async def on_meeting_end(context: TeamsTurnContext, state, meeting: MeetingDetails):
    ...

@teams.meetings.participants_join
async def on_participants_join(context: TeamsTurnContext, state, details: MeetingParticipantsEventDetails):
    ...

@teams.meetings.participants_leave
async def on_participants_leave(context: TeamsTurnContext, state, details: MeetingParticipantsEventDetails):
    ...
```

### Channel Events

```python
@teams.channels.created
async def on_channel_created(context: TeamsTurnContext, state, data: ChannelData):
    ...

@teams.channels.renamed
async def on_channel_renamed(context: TeamsTurnContext, state, data: ChannelData):
    ...

# Also available: deleted, shared, unshared, restored, members_added, members_removed
```

### Team Events

```python
@teams.teams.renamed
async def on_team_renamed(context: TeamsTurnContext, state, data: ChannelData):
    ...

# Also available: archived, unarchived, deleted, hard_deleted, restored
```

### File Consent

```python
@teams.file_consent.accept
async def on_file_accept(context: TeamsTurnContext, state, consent: FileConsentCardResponse):
    ...

@teams.file_consent.decline
async def on_file_decline(context: TeamsTurnContext, state, consent: FileConsentCardResponse):
    ...
```

### Config Invokes

```python
@teams.config.fetch
async def on_config_fetch(context: TeamsTurnContext, state, data):
    return ConfigResponse(...)

@teams.config.submit
async def on_config_submit(context: TeamsTurnContext, state, data):
    return ConfigResponse(...)
```

### Message Updates

```python
@teams.messages.edit
async def on_message_edit(context: TeamsTurnContext, state):
    ...

@teams.messages.delete
async def on_message_delete(context: TeamsTurnContext, state):
    ...

@teams.messages.read_receipt
async def on_read_receipt(context: TeamsTurnContext, state, data: dict):
    ...

@teams.messages.execute_action
async def on_execute_action(context: TeamsTurnContext, state, query: O365ConnectorCardActionQuery):
    ...
```

## Features Supported

- **Messaging Extensions** — query, fetch action, submit action, link unfurling, anonymous link unfurling, settings URL, configure settings, card button clicked, bot message preview (edit/send)
- **Task Modules** — fetch and submit with optional verb matching
- **Meeting Lifecycle** — start, end, participant join/leave
- **Channel Management** — created, deleted, renamed, shared, unshared, restored, members added/removed
- **Team Management** — archived, unarchived, deleted, hard deleted, renamed, restored
- **File Consent** — accept and decline flows
- **Config Invokes** — `config/fetch` and `config/submit`
- **Message Updates** — edit, delete, undelete, read receipts, actionable message execute
- **TeamsAgentExtension routing** — wraps any `AgentApplication` with zero configuration

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 💡 [Python Samples Repository](https://github.com/microsoft/Agents/tree/main/samples/python)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

# Sample Applications

|Name|Description|README|
|----|----|----|
|Quickstart|Simplest agent|[Quickstart](https://github.com/microsoft/Agents/blob/main/samples/python/quickstart/README.md)|
|Auto Sign In|Simple OAuth agent using Graph and GitHub|[auto-signin](https://github.com/microsoft/Agents/blob/main/samples/python/auto-signin/README.md)|
|OBO Authorization|OBO flow to access a Copilot Studio Agent|[obo-authorization](https://github.com/microsoft/Agents/blob/main/samples/python/obo-authorization/README.md)|
|Semantic Kernel Integration|A weather agent built with Semantic Kernel|[semantic-kernel-multiturn](https://github.com/microsoft/Agents/blob/main/samples/python/semantic-kernel-multiturn/README.md)|
|Streaming Agent|Streams OpenAI responses|[azure-ai-streaming](https://github.com/microsoft/Agents/blob/main/samples/python/azureai-streaming/README.md)|
|Copilot Studio Client|Console app to consume a Copilot Studio Agent|[copilotstudio-client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/README.md)|
|Cards Agent|Agent that uses rich cards to enhance conversation design|[cards](https://github.com/microsoft/Agents/blob/main/samples/python/cards/README.md)|

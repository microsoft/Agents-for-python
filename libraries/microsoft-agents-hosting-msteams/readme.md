# microsoft-agents-hosting-msteams

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/)

Teams-specific extension for the Microsoft 365 Agents SDK for Python. Provides the `TeamsAgentExtension` and a full set of typed, decorator-based route registrars for every Teams invoke and event activity — messaging extensions, task modules, meeting lifecycle events, channel and team management, file consent, config invokes, and more.

All handlers receive a `TeamsTurnContext`, a Teams-aware wrapper around the base `TurnContext` that surfaces the Teams API client and typed activity helpers.

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
| `TeamsTurnContext` | Teams-aware context passed to every handler. Provides the Teams API client and typed `TeamsActivity` helpers. |
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
from microsoft_agents.hosting.core import AgentApplication, TurnState
from microsoft_agents.hosting.msteams import TeamsAgentExtension

app = AgentApplication[TurnState]()
teams = TeamsAgentExtension(app)
```

`TeamsAgentExtension` registers a `before_turn` hook that deserializes `activity.channel_data` into a typed `ChannelData` object and creates a pre-authenticated Teams API client on the turn state for every Teams activity.

### The Teams context

Every handler registered through `TeamsAgentExtension` receives a `TeamsTurnContext` instead of a plain `TurnContext`.

#### `context.activity` → `TeamsActivity`

The activity is upgraded to `TeamsActivity`, which adds helper methods on top of the standard `Activity`:

```python
# Get the Teams channel the activity came from
channel_id = context.activity.get_channel_id()

# Get the team info embedded in channel_data
team = context.activity.get_team_info()

# Get the meeting the activity was sent in
meeting = context.activity.get_meeting_info()

# Mark the outgoing reply to target a specific user in a meeting
context.activity.notify_user(alert_in_meeting=True)

# Attach a feedback loop to a message being sent (Copilot scenarios)
context.activity.enable_feedback_loop()
```

#### `context.api_client` → `ApiClient`

Direct access to the Teams REST API client, pre-authenticated for the current turn. See [Teams API client](#teams-api-client) below.

#### Sending targeted activities

`TeamsTurnContext` adds two methods for sending activities that target a specific user in a meeting:

```python
await context.send_targeted_activity(activity)
await context.send_targeted_activities([activity1, activity2])
```

### Messaging Extensions

```python
from microsoft_teams.api.models import (
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    AppBasedLinkQuery,
)

# Search-based extension
@teams.message_extensions.query("searchCmd")
async def on_search(context: TeamsTurnContext, state, query: MessagingExtensionQuery):
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

# Anonymous link unfurling (before the user has authenticated)
@teams.message_extensions.anonymous_query_link
async def on_anon_link(context: TeamsTurnContext, state, query: AppBasedLinkQuery):
    return MessagingExtensionResponse(...)

# Bot message preview — edit stage
@teams.message_extensions.message_preview_edit("myCmd")
async def on_preview_edit(context: TeamsTurnContext, state, preview: Activity):
    return MessagingExtensionResponse(...)

# Bot message preview — send stage
@teams.message_extensions.message_preview_send("myCmd")
async def on_preview_send(context: TeamsTurnContext, state, preview: Activity):
    return MessagingExtensionResponse(...)

# Select item from search results
@teams.message_extensions.select_item
async def on_select_item(context: TeamsTurnContext, state, item):
    return MessagingExtensionResponse(...)

# Card button clicked
@teams.message_extensions.card_button_clicked
async def on_card_click(context: TeamsTurnContext, state, card):
    ...
```

All `command_id` arguments accept a plain string, a compiled `re.Pattern`, or `None` to match all commands.

#### Settings page

```python
@teams.message_extensions.query_setting_url
async def on_settings_url(context: TeamsTurnContext, state, query: MessagingExtensionQuery):
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(type="config", suggested_actions=...)
    )

@teams.message_extensions.setting
async def on_settings_submit(context: TeamsTurnContext, state, query: MessagingExtensionQuery):
    await save_settings(context, query.state)
```

### Task Modules

```python
from microsoft_teams.api.models import TaskModuleRequest, TaskModuleResponse

@teams.task_modules.fetch("myVerb")
async def on_task_fetch(context: TeamsTurnContext, state, request: TaskModuleRequest):
    return TaskModuleResponse(...)

@teams.task_modules.submit("myVerb")
async def on_task_submit(context: TeamsTurnContext, state, request: TaskModuleRequest):
    return TaskModuleResponse(...)
```

The first argument is a verb — a string or regex matched against `activity.value.data.verb`. Omit it to match all `task/fetch` or `task/submit` invokes.

### Meeting Events

```python
from microsoft_teams.api.models import MeetingDetails
from microsoft_agents.activity.teams import MeetingParticipantsEventDetails

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
from microsoft_teams.api.models import ChannelInfo

@teams.channels.created
async def on_channel_created(context: TeamsTurnContext, state, channel: ChannelInfo):
    print(f"New channel: {channel.name}")

@teams.channels.renamed
async def on_channel_renamed(context: TeamsTurnContext, state, channel: ChannelInfo):
    ...

# Also available: deleted, shared, unshared, restored, members_added, members_removed
```

`teams.channels.event()` is a catch-all that matches any `channel.*` event type via regex.

### Team Events

```python
from microsoft_teams.api.models import TeamInfo

@teams.teams.renamed
async def on_team_renamed(context: TeamsTurnContext, state, team: TeamInfo): ...

# Also available: archived, unarchived, deleted, hard_deleted, restored
```

`teams.teams.event()` is a catch-all matching any `team.*` event type.

### File Consent

```python
from microsoft_teams.api.models import FileConsentCardResponse

@teams.file_consent.accept
async def on_file_accept(context: TeamsTurnContext, state, consent: FileConsentCardResponse):
    await upload_file(consent.upload_info)

@teams.file_consent.decline
async def on_file_decline(context: TeamsTurnContext, state, consent: FileConsentCardResponse):
    ...
```

Teams expects a 200 OK with no body for both; the routing layer sends that automatically.

### Config Invokes

```python
from microsoft_teams.api.models import ConfigResponse

@teams.config.fetch
async def on_config_fetch(context: TeamsTurnContext, state, config_data):
    return ConfigResponse(...)

@teams.config.submit
async def on_config_submit(context: TeamsTurnContext, state, config_data):
    return ConfigResponse(...)
```

`config_data` is the raw `activity.value` payload.

### Message Updates

```python
from microsoft_teams.api.models import O365ConnectorCardActionQuery

@teams.messages.edit
async def on_message_edit(context: TeamsTurnContext, state):
    ...

@teams.messages.delete
async def on_message_delete(context: TeamsTurnContext, state):
    ...

@teams.messages.undelete
async def on_message_undelete(context: TeamsTurnContext, state):
    ...

@teams.messages.read_receipt
async def on_read_receipt(context: TeamsTurnContext, state, data: dict):
    last_read_id = data.get("lastReadMessageId")
    ...

@teams.messages.execute_action
async def on_execute_action(context: TeamsTurnContext, state, query: O365ConnectorCardActionQuery):
    ...
```

### Generic Teams routes

`TeamsAgentExtension` also wraps the underlying `AgentApplication` route methods so all handlers automatically receive a `TeamsTurnContext`:

```python
from microsoft_agents.activity import ActivityTypes, ConversationUpdateTypes

@teams.activity(ActivityTypes.message)
async def on_any_message(context: TeamsTurnContext, state):
    await context.send_activity(f"Echo: {context.activity.text}")

@teams.message(r"^hello")
async def on_hello(context: TeamsTurnContext, state):
    await context.send_activity("Hi there!")

@teams.conversation_update(ConversationUpdateTypes.members_added)
async def on_members_added(context: TeamsTurnContext, state):
    for member in context.activity.members_added:
        if member.id != context.activity.recipient.id:
            await context.send_activity(f"Welcome, {member.name}!")
```

## Teams API client

`context.api_client` is a pre-authenticated `ApiClient` pointing at the Teams connector service for the current turn. It wraps the Teams REST API and is the right tool for operations on channels, conversations, and members.

```python
# Get the list of members in the current conversation
members = await context.api_client.conversations.get_conversation_members(
    context.activity.conversation.id
)

# Send a proactive message to a specific conversation
await context.api_client.conversations.send_to_conversation(
    context.activity.conversation.id,
    activity,
)
```

You can also get the client directly from the extension if you have a context but aren't inside a Teams handler:

```python
client = teams.get_teams_api_client(context)
```

## Microsoft Graph client

For operations that go beyond the Teams connector service — user profiles, SharePoint, calendar, etc. — use the Graph client:

```python
@teams.message(r"^profile")
async def on_profile(context: TeamsTurnContext, state):
    graph = teams.get_graph_client(context, handler_name="UserAuth")
    user = await graph.users.by_user_id(context.activity.from_.aad_object_id).get()
    await context.send_activity(f"Display name: {user.display_name}")
```

The `handler_name` argument names an OAuth connection configured in the app's `auth` settings. If omitted, the app's default auth handler is used.

## Invoke response conventions

Teams expects a synchronous HTTP response for all invoke activities. The routing layer handles this automatically — return a value from your handler and the framework serializes and sends it.

| Namespace | Sends response? | Response type |
|---|---|---|
| `task_modules.fetch/submit` | If handler returns non-`None` | `TaskModuleResponse` |
| `message_extensions.query/select_item/fetch_action/submit_action/message_preview_*` | If handler returns non-`None` | `MessagingExtensionResponse` / `MessagingExtensionActionResponse` |
| `message_extensions.query_link/anonymous_query_link/query_setting_url` | If handler returns non-`None` | `MessagingExtensionResponse` |
| `message_extensions.setting` | Always | `MessagingExtensionResponse` (or 200 with no body if handler returns `None`) |
| `message_extensions.card_button_clicked` | Always | empty 200 |
| `config.fetch/submit` | If handler returns non-`None` | `ConfigResponse` |
| `file_consent.accept/decline` | Always | empty 200 |
| `messages.execute_action` | Always | empty 200 |
| `meetings`, `channels`, `teams`, `messages.edit/undelete/delete` | Never — not invokes | — |

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

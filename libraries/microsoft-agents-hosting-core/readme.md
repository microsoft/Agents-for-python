# Microsoft Agents Hosting Core

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/)

The core hosting library for Microsoft 365 Agents SDK. This library provides the fundamental building blocks for creating conversational AI agents, including activity processing, state management, authentication, and channel communication.

This is the heart of the Microsoft 365 Agents SDK - think of it as the engine that powers your conversational agents. It handles the complex orchestration of conversations, manages state across turns, and provides the infrastructure needed to build production-ready agents that work across Microsoft 365 platforms.

# What is this?
This library is part of the **Microsoft 365 Agents SDK for Python** - a comprehensive framework for building enterprise-grade conversational AI agents. The SDK enables developers to create intelligent agents that work across multiple platforms including Microsoft Teams, M365 Copilot, Copilot Studio, and web chat, with support for third-party integrations like Slack, Facebook Messenger, and Twilio.

## Release Notes
<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>0.5.0</td>
    <td>2025-10-22</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md">
        0.5.0 Release Notes
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
| `microsoft-agents-hosting-teams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-teams)](https://pypi.org/project/microsoft-agents-hosting-teams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |

Additionally we provide a Copilot Studio Client, to interact with Agents created in CopilotStudio:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-copilotstudio-client` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/) | Direct to Engine client to interact with Agents created in CopilotStudio |


## Installation

```bash
pip install microsoft-agents-hosting-core
```
## Simple Echo Agent
See the [Quickstart sample](https://github.com/microsoft/Agents/tree/main/samples/python/quickstart) for full working code.

```python
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

...

start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
```

## Core Concepts

### AgentApplication vs ActivityHandler

**AgentApplication** - Modern, fluent API for building agents:
- Decorator-based routing (`@agent_app.activity("message")`)
- Built-in state management and middleware
- AI-ready with authorization support
- Type-safe with generics

**ActivityHandler** - Traditional inheritance-based approach:
- Override methods for different activity types
- More familiar to Bot Framework developers
- Lower-level control over activity processing

### Route-based Message Handling

```python
@AGENT_APP.message(re.compile(r"^hello$"))
async def on_hello(context: TurnContext, _state: TurnState):
    await context.send_activity("Hello!")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(f"you said: {context.activity.text}")
```

### Error Handling

```python
@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
```


## Key Classes Reference

### Core Classes
- **`AgentApplication`** - Main application class with fluent API
- **`ActivityHandler`** - Base class for inheritance-based agents
- **`TurnContext`** - Context for each conversation turn
- **`TurnState`** - State management across conversation turns

### State Management
- **`ConversationState`** - Conversation-scoped state
- **`UserState`** - User-scoped state across conversations
- **`TempState`** - Temporary state for current turn
- **`MemoryStorage`** - In-memory storage (development)

### Messaging
- **`MessageFactory`** - Create different types of messages
- **`CardFactory`** - Create rich card attachments
- **`InputFile`** - Handle file attachments

### Authorization
- **`Authorization`** - Authentication and authorization manager
- **`ClaimsIdentity`** - User identity and claims

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
|Cards Agent|Agent that uses rich cards to enhance conversation design |[cards](https://github.com/microsoft/Agents/blob/main/samples/python/cards/README.md)|
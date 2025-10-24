# Microsoft Agents Hosting - aiohttp

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/)

Integration library for hosting Microsoft 365 Agents using aiohttp. This library provides HTTP adapters, middleware, and utilities for building web-based agent applications with the popular aiohttp framework.

This library bridges the Microsoft 365 Agents SDK with aiohttp, allowing you to create HTTP endpoints that handle agent conversations. It provides everything you need to host agents as web services, including request processing, authentication, and routing.

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
pip install microsoft-agents-hosting-aiohttp
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


### Error Handling

Customize error responses. Code take from the [Quickstart sample](https://github.com/microsoft/Agents/tree/main/samples/python/quickstart). 

```python
@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
```

## Features

✅ **HTTP hosting** - Full aiohttp integration for web hosting  
✅ **JWT authentication** - Built-in security with middleware  
✅ **Agent-to-agent** - Support for multi-agent communication  
✅ **Streaming** - Real-time response streaming  
✅ **Error handling** - Comprehensive error management  
✅ **Development friendly** - Hot reload and debugging support

## Requirements

- Python 3.10+ (supports 3.10, 3.11, 3.12, 3.13, 3.14)
- aiohttp 3.11.11+
- Microsoft Agents hosting core library

## Best Practices

1. **Use middleware** for cross-cutting concerns like auth and logging
2. **Handle errors gracefully** with custom error handlers
3. **Secure your endpoints** with JWT middleware in production
4. **Structure routes** logically for agent communication

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
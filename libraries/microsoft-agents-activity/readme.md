# Microsoft Agents Activity

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/)

Core types and schemas for building conversational AI agents that work across Microsoft 365 platforms like Teams, Copilot Studio, and Webchat.

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

## Architecture

The SDK follows a modular architecture:
- **Activity Layer**: Protocol definitions for cross-platform messaging
- **Hosting Layer**: Core agent lifecycle, middleware, and web hosting
- **Storage Layer**: Persistent state management with Azure backends
- **Authentication Layer**: Secure identity and token management
- **Integration Layer**: Platform-specific adapters (Teams, Copilot Studio)

## Installation

```bash
pip install microsoft-agents-activity
```

## Quick Start
Code below taken from the [Quick Start](https://github.com/microsoft/Agents/tree/main/samples/python/quickstart) sample.
```python
@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the empty agent! "
        "This agent is designed to be a starting point for your own agent development."
    )
    return True


@AGENT_APP.message(re.compile(r"^hello$"))
async def on_hello(context: TurnContext, _state: TurnState):
    await context.send_activity("Hello!")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(f"you said: {context.activity.text}")
```

## Common Use Cases

### Rich Messages with Cards
Code below taken from the [Cards](https://github.com/microsoft/Agents/tree/main/samples/python/cards) sample.


```python
    @staticmethod
    async def send_animation_card(context: TurnContext):
        card = CardFactory.animation_card(
            AnimationCard(
                title="Microsoft Agents Framework",
                image=ThumbnailUrl(
                    url="https://i.giphy.com/Ki55RUbOV5njy.gif", alt="Cute Robot"
                ),
                media=[MediaUrl(url="https://i.giphy.com/Ki55RUbOV5njy.gif")],
                subtitle="Animation Card",
                text="This is an example of an animation card using a gif.",
                aspect="16:9",
                duration="PT2M",
            )
        )
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_activity(context: TurnContext, card: Attachment):
        activity = Activity(type=ActivityTypes.message, attachments=[card])
        await context.send_activity(activity)
```

## Activity Types

The library supports different types of communication:

- **Message** - Regular chat messages with text, cards, attachments
- **Typing** - Show typing indicators  
- **ConversationUpdate** - People joining/leaving chats
- **Event** - Custom events and notifications
- **Invoke** - Direct function calls
- **EndOfConversation** - End chat sessions

## Key Features

✅ **Type-safe** - Built with Pydantic for automatic validation  
✅ **Rich content** - Support for cards, images, videos, and interactive elements  
✅ **Teams ready** - Full Microsoft Teams integration  
✅ **Cross-platform** - Works across all Microsoft 365 chat platforms  
✅ **Migration friendly** - Easy upgrade from Bot Framework  

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 💡 [Python Samples Repository](https://github.com/microsoft/Agents/tree/main/samples/python)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

# Sample Applications
Explore working examples in the [Python samples repository](https://github.com/microsoft/Agents/tree/main/samples/python):

|Name|Description|README|
|----|----|----|
|Quickstart|Simplest agent|[Quickstart](https://github.com/microsoft/Agents/blob/main/samples/python/quickstart/README.md)|
|Auto Sign In|Simple OAuth agent using Graph and GitHub|[auto-signin](https://github.com/microsoft/Agents/blob/main/samples/python/auto-signin/README.md)|
|OBO Authorization|OBO flow to access a Copilot Studio Agent|[obo-authorization](https://github.com/microsoft/Agents/blob/main/samples/python/obo-authorization/README.md)|
|Semantic Kernel Integration|A weather agent built with Semantic Kernel|[semantic-kernel-multiturn](https://github.com/microsoft/Agents/blob/main/samples/python/semantic-kernel-multiturn/README.md)|
|Streaming Agent|Streams OpenAI responses|[azure-ai-streaming](https://github.com/microsoft/Agents/blob/main/samples/python/azureai-streaming/README.md)|
|Copilot Studio Client|Console app to consume a Copilot Studio Agent|[copilotstudio-client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/README.md)|
|Cards Agent|Agent that uses rich cards to enhance conversation design |[cards](https://github.com/microsoft/Agents/blob/main/samples/python/cards/README.md)|
# Microsoft Agents Activity

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/)

Core types and schemas for building conversational AI agents that work across Microsoft 365 platforms like Teams, Copilot Studio, and Webchat.

# What is this?

This library is part of the **Microsoft 365 Agents SDK for Python** - a comprehensive framework for building enterprise-grade conversational AI agents. The SDK enables developers to create intelligent agents that work across multiple platforms including Microsoft Teams, M365 Copilot, Copilot Studio, and web chat, with support for third-party integrations like Slack, Facebook Messenger, and Twilio.

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

```python
from microsoft_agents.activity import Activity, ActivityTypes

# Send a simple message
activity = Activity(
    type=ActivityTypes.message,
    text="Hello! How can I help you today?"
)

# Create a reply
reply = activity.create_reply("Thanks for reaching out!")

# Show typing indicator
typing = Activity.create_typing_activity()
```

## Common Use Cases

### Rich Messages with Cards

```python
from microsoft_agents.activity import HeroCard, CardAction, Attachment

# Create a welcome card
card = HeroCard(
    title="Welcome to our service!",
    subtitle="Let's get you started",
    text="Choose an option below to continue",
    actions=[
        CardAction(type="imBack", title="Get Help", value="help"),
        CardAction(type="imBack", title="View Profile", value="profile")
    ]
)

activity = Activity(
    type=ActivityTypes.message,
    text="Welcome!",
    attachments=[Attachment(
        content_type="application/vnd.microsoft.card.hero",
        content=card
    )]
)
```

### Handle @Mentions

```python
from microsoft_agents.activity import Mention, ChannelAccount

# Check for mentions in incoming messages
mentions = activity.get_mentions()
for mention in mentions:
    mentioned_user = mention.mentioned
    print(f"User {mentioned_user.name} was mentioned")
```

### Teams Integration

```python
from microsoft_agents.activity.teams import TeamsChannelAccount

# Work with Teams-specific user info
teams_user = TeamsChannelAccount(
    id="user123",
    name="John Doe",
    user_principal_name="john.doe@company.com"
)
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
- **Teams Agent**: Full-featured Microsoft Teams bot with SSO and adaptive cards
- **Copilot Studio Integration**: Connect to Copilot Studio agents
- **Multi-Channel Agent**: Deploy to Teams, webchat, and third-party platforms
- **Authentication Flows**: OAuth, MSAL, and token management examples
- **State Management**: Conversation and user state with Azure storage
- **Streaming Responses**: Real-time agent responses with citations
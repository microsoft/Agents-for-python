# Microsoft Agents Activity

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/)

Core types and schemas for building conversational AI agents that work across Microsoft 365 platforms like Teams, Copilot Studio, and Webchat.

## What is this?

This library provides the fundamental building blocks for agent communication - think of it as the "language" that agents use to talk to each other and to users. An Activity is basically a message, event, or action in a conversation.

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

## Need Help?

- 📖 [Full SDK Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
- 💬 [Ask Questions](https://stackoverflow.com/questions/tagged/microsoft-agents)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.
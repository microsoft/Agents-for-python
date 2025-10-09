# Microsoft Agents Hosting Core

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/)

The core hosting library for Microsoft 365 Agents SDK. This library provides the fundamental building blocks for creating conversational AI agents, including activity processing, state management, authentication, and channel communication.

This is the heart of the Microsoft 365 Agents SDK - think of it as the engine that powers your conversational agents. It handles the complex orchestration of conversations, manages state across turns, and provides the infrastructure needed to build production-ready agents that work across Microsoft 365 platforms.

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


## Installation

```bash
pip install microsoft-agents-hosting-core
```

## Quick Start

### Simple Echo Agent

```python
from microsoft_agents.hosting.core import (
    AgentApplication, 
    TurnState, 
    TurnContext, 
    MemoryStorage
)

# Create your agent application
storage = MemoryStorage()
agent_app = AgentApplication[TurnState](storage=storage)

@agent_app.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

# Agent is ready to process messages!
```

### Activity Handler Style

```python
from microsoft_agents.hosting.core import ActivityHandler, TurnContext

class MyAgent(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Hello from ActivityHandler!")
    
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Welcome to the conversation!")

agent = MyAgent()
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

### Turn Context

Every conversation "turn" (message exchange) gets a `TurnContext` containing:

```python
async def handle_message(context: TurnContext, state: TurnState):
    # The incoming activity (message, event, etc.)
    user_message = context.activity.text
    
    # Send responses
    await context.send_activity("Simple text response")
    
    # Send rich content
    from microsoft_agents.hosting.core import MessageFactory
    card_activity = MessageFactory.attachment(hero_card)
    await context.send_activity(card_activity)
    
    # Access conversation metadata
    conversation_id = context.activity.conversation.id
    user_id = context.activity.from_property.id
```

### State Management

Agents need to remember information across conversation turns:

```python
from microsoft_agents.hosting.core import (
    TurnState, 
    ConversationState, 
    UserState,
    MemoryStorage
)

storage = MemoryStorage()
agent_app = AgentApplication[TurnState](storage=storage)

@agent_app.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    # Conversation-scoped data (shared by all users in conversation)
    conversation_data = state.conversation
    conversation_data.set_value("topic", "weather")
    
    # User-scoped data (specific to this user across conversations)
    user_data = state.user
    user_data.set_value("name", "John")
    
    # Temporary data (only for this turn)
    state.temp.set_value("processing_step", "validation")
    
    # State is automatically saved after the turn
```

#### Built-in State Scopes

- **ConversationState** - Shared across all users in a conversation
- **UserState** - Specific to individual users across all conversations  
- **TempState** - Temporary data for the current turn only

## Advanced Features

### Route-based Message Handling

```python
# Handle all messages
@agent_app.activity("message")
async def handle_all_messages(context: TurnContext, state: TurnState):
    await context.send_activity("Default handler")

# Handle specific patterns
@agent_app.message(r"/weather (\w+)")
async def handle_weather(context: TurnContext, state: TurnState):
    city = context.matches[1]  # Extract from regex
    await context.send_activity(f"Weather for {city}")

# Handle conversation updates
@agent_app.conversation_update("membersAdded")
async def welcome_user(context: TurnContext, state: TurnState):
    await context.send_activity("Welcome to the agent!")

# Handle different activity types
@agent_app.activity("event")
async def handle_events(context: TurnContext, state: TurnState):
    event_name = context.activity.name
    await context.send_activity(f"Received event: {event_name}")
```

### Authentication & Authorization

```python
from microsoft_agents.hosting.core import Authorization
from microsoft_agents.authentication.msal import MsalConnectionManager

# Set up authentication
connection_manager = MsalConnectionManager(**config)
authorization = Authorization(storage, connection_manager, **config)

agent_app = AgentApplication[TurnState](
    storage=storage,
    authorization=authorization,
    **config
)

@agent_app.activity("message")
async def authenticated_handler(context: TurnContext, state: TurnState):
    # Check if user is authenticated
    if not agent_app.auth.is_signed_in(context):
        await agent_app.auth.sign_in(context)
        return
    
    # Get user token for Microsoft Graph
    token = await agent_app.auth.get_token(context, ["User.Read"])
    # Use token to call Microsoft Graph APIs
```

### Middleware & Logging

```python
from microsoft_agents.hosting.core.storage import (
    TranscriptLoggerMiddleware, 
    ConsoleTranscriptLogger
)

# Add transcript logging
adapter.use(TranscriptLoggerMiddleware(ConsoleTranscriptLogger()))

# Custom middleware
class CustomMiddleware:
    async def on_turn(self, context: TurnContext, next_handler):
        print(f"Before: {context.activity.text}")
        await next_handler()
        print("After: Turn completed")

adapter.use(CustomMiddleware())
```

### File Handling

```python
from microsoft_agents.hosting.core import InputFile

@agent_app.activity("message")
async def handle_files(context: TurnContext, state: TurnState):
    # Check for file attachments
    files = state.temp.input_files
    if files:
        for file in files:
            if file.content_type.startswith("image/"):
                # Process image file
                content = await file.download()
                await context.send_activity(f"Received image: {file.name}")
```

### Error Handling

```python
@agent_app.error
async def on_error(context: TurnContext, error: Exception):
    print(f"Error occurred: {error}")
    await context.send_activity("Sorry, something went wrong.")

# Custom error types
from microsoft_agents.hosting.core import ApplicationError

async def risky_operation():
    if something_wrong:
        raise ApplicationError("Custom error message")
```

## Storage Options

### Memory Storage (Development)

```python
from microsoft_agents.hosting.core import MemoryStorage

storage = MemoryStorage()  # Data lost when app restarts
```

### Persistent Storage (Production)

```python
# Azure Blob Storage
from microsoft_agents.storage.blob import BlobStorage
storage = BlobStorage("connection_string", "container_name")

# Azure Cosmos DB
from microsoft_agents.storage.cosmos import CosmosDbStorage  
storage = CosmosDbStorage("connection_string", "database", "container")
```

## Channel Communication

### Agent-to-Agent Communication

```python
from microsoft_agents.hosting.core import (
    HttpAgentChannelFactory,
    ConfigurationChannelHost
)

# Set up agent communication
channel_factory = HttpAgentChannelFactory()
channel_host = ConfigurationChannelHost(
    channel_factory, connection_manager, config, "HttpAgentClient"
)

# Send message to another agent
await channel_host.send_to_agent(
    agent_id="other-agent-id",
    activity=message_activity
)
```

### Teams Integration

```python
from microsoft_agents.hosting.teams import TeamsActivityHandler

class TeamsAgent(TeamsActivityHandler):
    async def on_teams_message_activity(self, turn_context: TurnContext):
        # Teams-specific message handling
        await turn_context.send_activity("Hello from Teams!")
    
    async def on_teams_members_added_activity(self, turn_context: TurnContext):
        # Handle new team members
        await turn_context.send_activity("Welcome to the team!")
```

## Rich Content Creation

### Message Factory

```python
from microsoft_agents.hosting.core import MessageFactory

# Simple text
message = MessageFactory.text("Hello world!")

# Text with suggested actions
message = MessageFactory.suggested_actions(
    ["Option 1", "Option 2", "Option 3"],
    "Choose an option:"
)

# Attachment (cards, files, etc.)
message = MessageFactory.attachment(hero_card_attachment)
```

### Card Factory

```python
from microsoft_agents.hosting.core import CardFactory

# Hero card
hero_card = CardFactory.hero_card(
    title="Card Title",
    subtitle="Card Subtitle", 
    text="Card description text",
    images=["https://example.com/image.jpg"],
    buttons=[
        {"type": "imBack", "title": "Click Me", "value": "button_clicked"}
    ]
)

# Adaptive card
adaptive_card = CardFactory.adaptive_card({
    "type": "AdaptiveCard",
    "version": "1.2",
    "body": [
        {
            "type": "TextBlock",
            "text": "Hello Adaptive Cards!"
        }
    ]
})
```

## Configuration & Deployment

### Environment Setup

```python
import os
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AgentApplication, TurnState

# Load from environment variables
config = load_configuration_from_env(os.environ)

# Create fully configured agent
agent_app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    authorization=authorization,
    **config
)
```

### Application Options

```python
from microsoft_agents.hosting.core import ApplicationOptions

options = ApplicationOptions(
    agent_id="my-agent",
    storage=storage,
    authentication=auth_config,
    logging_level="DEBUG"
)

agent_app = AgentApplication[TurnState](options=options)
```

## Architecture Patterns

### Layered Architecture

```python
# Domain layer - business logic
class WeatherService:
    async def get_weather(self, city: str) -> str:
        return f"Weather in {city}: Sunny, 72°F"

# Application layer - agent handlers
@agent_app.message(r"/weather (\w+)")
async def weather_handler(context: TurnContext, state: TurnState):
    city = context.matches[1]
    weather_service = WeatherService()
    weather = await weather_service.get_weather(city)
    await context.send_activity(weather)
```

### State Management Patterns

```python
# Custom state scope
class OrderState(AgentState):
    def get_storage_key(self, turn_context: TurnContext):
        return f"order:{turn_context.activity.from_property.id}"

# Use custom state
custom_state = OrderState(storage, "OrderState")
turn_state = TurnState.with_storage(storage, custom_state)
```

### Plugin Architecture

```python
# Create reusable components
class GreetingPlugin:
    @staticmethod
    def register(app: AgentApplication):
        @app.conversation_update("membersAdded")
        async def greet(context: TurnContext, state: TurnState):
            await context.send_activity("Welcome!")

# Register plugins
GreetingPlugin.register(agent_app)
```

## Testing Your Agents

### Unit Testing

```python
import pytest
from microsoft_agents.hosting.core import TurnContext, MemoryStorage
from microsoft_agents.activity import Activity, ActivityTypes

@pytest.mark.asyncio
async def test_echo_handler():
    # Create test activity
    activity = Activity(
        type=ActivityTypes.message,
        text="test message",
        conversation={"id": "test"},
        from_property={"id": "user"}
    )
    
    # Create test context
    context = TurnContext(mock_adapter, activity)
    state = TurnState.with_storage(MemoryStorage())
    
    # Test your handler
    await echo_handler(context, state)
    
    # Verify response
    assert len(context.responses) == 1
    assert "test message" in context.responses[0].text
```

### Integration Testing

```python
# Test with real storage and authentication
async def test_authenticated_flow():
    storage = MemoryStorage()
    agent_app = AgentApplication[TurnState](
        storage=storage,
        authorization=test_auth
    )
    
    # Simulate authenticated conversation
    context = create_test_context(authenticated_user_activity)
    await agent_app.on_turn(context)
```

## Performance & Best Practices

### Efficient State Management

```python
# Load only needed state scopes
minimal_state = TurnState()
minimal_state.add(ConversationState(storage))  # Only add what you need

# Batch state operations
async def batch_operations(context: TurnContext, state: TurnState):
    state.conversation.set_value("key1", "value1")
    state.conversation.set_value("key2", "value2")
    state.user.set_value("preference", "dark_mode")
    # All saved together at end of turn
```

### Async Best Practices

```python
@agent_app.activity("message")
async def efficient_handler(context: TurnContext, state: TurnState):
    # Good: Use async/await for I/O operations
    api_result = await external_api_call()
    
    # Good: Process concurrently when possible
    results = await asyncio.gather(
        call_service_a(),
        call_service_b(),
        call_service_c()
    )
    
    await context.send_activity(f"Results: {results}")
```

### Error Recovery

```python
@agent_app.activity("message")
async def resilient_handler(context: TurnContext, state: TurnState):
    try:
        result = await unreliable_service()
        await context.send_activity(f"Success: {result}")
    except ServiceError:
        # Graceful degradation
        await context.send_activity("Service temporarily unavailable, try again later")
    except Exception as e:
        # Log and provide user-friendly message
        logger.error(f"Unexpected error: {e}")
        await context.send_activity("Something went wrong, please try again")
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

## Migration from Bot Framework

| Bot Framework | Microsoft Agents Core |
|---------------|----------------------|
| `BotFrameworkAdapter` | `CloudAdapter` |
| `ActivityHandler` | `ActivityHandler` or `AgentApplication` |
| `TurnContext` | `TurnContext` |
| `ConversationState` | `ConversationState` |
| `UserState` | `UserState` |
| `MemoryStorage` | `MemoryStorage` |
| `MessageFactory` | `MessageFactory` |

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
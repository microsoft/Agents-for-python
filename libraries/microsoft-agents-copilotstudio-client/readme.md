# Microsoft Agents Copilot Studio Client

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/)

The Copilot Studio Client is for connecting to and interacting with agents created in Microsoft Copilot Studio. This library allows you to integrate Copilot Studio agents into your Python applications.

## What is this?

This client library provides a direct connection to Copilot Studio agents, bypassing traditional chat channels. It's perfect for integrating AI conversations into your applications, building custom UIs, or creating agent-to-agent communication flows.

## Installation

```bash
pip install microsoft-agents-copilotstudio-client
```

## Quick Start

### Basic Setup

```python
from microsoft_agents.copilotstudio.client import (
    CopilotClient, 
    ConnectionSettings, 
    PowerPlatformCloud, 
    AgentType
)

# Configure connection to your Copilot Studio agent
settings = ConnectionSettings(
    environment_id="your-environment-id",
    agent_identifier="your-agent-id", 
    cloud=PowerPlatformCloud.PROD,
    copilot_agent_type=AgentType.PUBLISHED
)

# Create client with access token
client = CopilotClient(settings, "your-access-token")
```

### Start a Conversation

```python
import asyncio

async def chat_with_agent():
    # Initialize conversation
    async for activity in client.start_conversation():
        if activity.type == "message":
            print(f"Agent: {activity.text}")
    
    # Send a question
    async for activity in client.ask_question("Hello, how can you help me?"):
        if activity.type == "message":
            print(f"Agent: {activity.text}")

# Run the conversation
asyncio.run(chat_with_agent())
```

## Configuration Options

### Connection Settings

```python
settings = ConnectionSettings(
    environment_id="12345678-1234-1234-1234-123456789012",  # Required
    agent_identifier="your-agent-name",                      # Required  
    cloud=PowerPlatformCloud.PROD,                          # Environment
    copilot_agent_type=AgentType.PUBLISHED                  # Agent version
)
```

### Power Platform Clouds

Choose the appropriate cloud environment:

```python
from microsoft_agents.copilotstudio.client import PowerPlatformCloud

# Production (default)
cloud = PowerPlatformCloud.PROD

# Government clouds
cloud = PowerPlatformCloud.GOV
cloud = PowerPlatformCloud.HIGH
cloud = PowerPlatformCloud.DOD

# Testing environments
cloud = PowerPlatformCloud.DEV
cloud = PowerPlatformCloud.TEST

# Custom cloud
settings = ConnectionSettings(
    environment_id="your-env-id",
    agent_identifier="your-agent-id",
    cloud=PowerPlatformCloud.OTHER,
    custom_power_platform_cloud="your-custom-cloud.powerplatform.com"
)
```

### Agent Types

```python
from microsoft_agents.copilotstudio.client import AgentType

# Published agent (default)
agent_type = AgentType.PUBLISHED

# Prebuilt agent
agent_type = AgentType.PREBUILT
```

## Authentication

### Get Access Token

You need a valid access token for the Power Platform API:

```python
from msal import PublicClientApplication

# MSAL configuration
app = PublicClientApplication(
    client_id="your-app-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id"
)

# Get token
result = app.acquire_token_interactive(
    scopes=["https://api.powerplatform.com/.default"]
)

if "access_token" in result:
    token = result["access_token"]
    client = CopilotClient(settings, token)
```

### Environment Variables

Set up your `.env` file:

```bash
# Required
ENVIRONMENT_ID=your-power-platform-environment-id
AGENT_IDENTIFIER=your-copilot-studio-agent-id
APP_CLIENT_ID=your-azure-app-client-id
TENANT_ID=your-azure-tenant-id

# Optional
CLOUD=PROD
COPILOT_AGENT_TYPE=PUBLISHED
CUSTOM_POWER_PLATFORM_CLOUD=your-custom-cloud.com
```

## Advanced Usage

### Send Custom Activities

```python
from microsoft_agents.activity import Activity, ActivityTypes, ConversationAccount

# Create custom activity
activity = Activity(
    type=ActivityTypes.message,
    text="Custom message with metadata",
    conversation=ConversationAccount(id="conversation-123"),
    value={"customData": "example"}
)

# Send to agent
async for response in client.ask_question_with_activity(activity):
    print(f"Response: {response.text}")
```

### Handle Different Activity Types

```python
async def handle_conversation():
    async for activity in client.start_conversation():
        if activity.type == "message":
            print(f"Message: {activity.text}")
            
            # Check for suggested actions
            if activity.suggested_actions:
                print("Available actions:")
                for action in activity.suggested_actions.actions:
                    print(f"  - {action.title}")
                    
        elif activity.type == "typing":
            print("Agent is typing...")
            
        elif activity.type == "event":
            print(f"Event: {activity.name}")
```

### Conversation Management

```python
class ConversationManager:
    def __init__(self, client: CopilotClient):
        self.client = client
        self.conversation_id = None
    
    async def start_new_conversation(self):
        async for activity in self.client.start_conversation():
            if activity.conversation:
                self.conversation_id = activity.conversation.id
            yield activity
    
    async def send_message(self, text: str):
        async for activity in self.client.ask_question(text, self.conversation_id):
            yield activity
```

## Integration with Microsoft 365 Agents SDK

```python
from microsoft_agents.hosting.core import TurnContext, MessageFactory
from microsoft_agents.authentication.msal import MsalAuth

# In your agent handler
async def handle_copilot_studio_query(context: TurnContext):
    # Get OBO token
    auth = MsalAuth(your_auth_config)
    token = await auth.acquire_token_on_behalf_of(
        scopes=["https://api.powerplatform.com/.default"],
        user_assertion="user-token"
    )
    
    # Create Copilot Studio client
    client = CopilotClient(settings, token)
    
    # Forward user message to Copilot Studio
    user_message = context.activity.text
    async for activity in client.ask_question(user_message):
        await context.send_activity(MessageFactory.text(activity.text))
```

## Console Chat Example

```python
async def console_chat():
    # Start conversation
    print("Starting conversation with Copilot Studio agent...")
    async for activity in client.start_conversation():
        if activity.type == "message":
            print(f"Agent: {activity.text}")
    
    # Chat loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        async for activity in client.ask_question(user_input):
            if activity.type == "message":
                print(f"Agent: {activity.text}")
```

## Key Classes

- **`CopilotClient`** - Main client for communicating with Copilot Studio agents
- **`ConnectionSettings`** - Configuration for connecting to your agent
- **`PowerPlatformCloud`** - Enum for different Power Platform environments
- **`AgentType`** - Enum for agent version types (published/prebuilt)

## Features

✅ **Real-time streaming** - Server-sent events for live responses  
✅ **Multi-cloud support** - Works across all Power Platform clouds  
✅ **Rich content** - Support for cards, actions, and attachments  
✅ **Conversation management** - Maintain context across interactions  
✅ **Custom activities** - Send structured data to agents  
✅ **Async/await** - Modern Python async support

## Troubleshooting

### Common Issues

**Authentication failed**
- Verify your app is registered in Azure AD
- Check that token has `https://api.powerplatform.com/.default` scope
- Ensure your app has permissions to the Power Platform environment

**Agent not found**
- Verify the environment ID and agent identifier
- Check that the agent is published and accessible
- Confirm you're using the correct cloud setting

**Connection timeout**
- Check network connectivity to Power Platform
- Verify firewall settings allow HTTPS traffic
- Try a different cloud region if available

## Requirements

- Python 3.9+
- Valid Azure AD app registration
- Access to Microsoft Power Platform environment
- Published Copilot Studio agent

## Need Help?

- 📖 [Copilot Studio Documentation](https://docs.microsoft.com/power-virtual-agents/)
- 🔧 [Power Platform Admin Center](https://admin.powerplatform.microsoft.com/)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
- 💬 [Sample Applications](https://github.com/microsoft/Agents-for-python/tree/main/test_samples/copilot_studio_client_sample)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.
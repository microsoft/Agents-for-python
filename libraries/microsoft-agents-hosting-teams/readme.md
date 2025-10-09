# Microsoft Agents Hosting - Teams

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-teams)](https://pypi.org/project/microsoft-agents-hosting-teams/)

Integration library for building Microsoft Teams agents using the Microsoft 365 Agents SDK. This library provides specialized handlers and utilities for Teams-specific functionality like messaging extensions, task modules, adaptive cards, and meeting events.

This library extends the core hosting capabilities with Teams-specific features. It handles Teams' unique interaction patterns like messaging extensions, tab applications, task modules, and meeting integrations. Think of it as the bridge that makes your agent "Teams-native" rather than just a generic chatbot.

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
pip install microsoft-agents-hosting-teams
```

## Quick Start

### Basic Teams Agent

```python
from microsoft_agents.hosting.teams import TeamsActivityHandler
from microsoft_agents.hosting.core import TurnContext, MessageFactory

class MyTeamsAgent(TeamsActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(
            MessageFactory.text("Hello from Teams!")
        )
    
    async def on_teams_members_added_activity(self, turn_context: TurnContext):
        for member in turn_context.activity.members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(f"Welcome to Teams, {member.name}!")
                )

# Use with hosting adapter
agent = MyTeamsAgent()
```

### Teams-Specific Features

```python
from microsoft_agents.hosting.teams import TeamsInfo

class TeamsAgent(TeamsActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.lower()
        
        if "team info" in text:
            # Get team member information
            team_id = turn_context.activity.channel_data.get("team", {}).get("id")
            member = await TeamsInfo.get_team_member(
                turn_context, team_id, turn_context.activity.from_property.id
            )
            await turn_context.send_activity(f"Member info: {member.name}")
        
        elif "send to channel" in text:
            # Send message to specific channel
            channel_id = "19:channel-id@thread.teams"
            activity = MessageFactory.text("Broadcasting to channel!")
            
            await TeamsInfo.send_message_to_teams_channel(
                turn_context, activity, channel_id
            )
```

## Core Components

### TeamsActivityHandler

The main class that extends `ActivityHandler` with Teams-specific event handling:

```python
class MyTeamsAgent(TeamsActivityHandler):
    # Standard message handling
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Got your message!")
    
    # Teams conversation events
    async def on_teams_members_added_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Welcome to the team!")
    
    async def on_teams_members_removed_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Someone left the team")
    
    # Meeting events
    async def on_teams_meeting_start(self, meeting_details, turn_context: TurnContext):
        await turn_context.send_activity("Meeting started!")
    
    async def on_teams_meeting_end(self, meeting_details, turn_context: TurnContext):
        await turn_context.send_activity("Meeting ended!")
```

### TeamsInfo Utilities

Helper class for Teams-specific operations:

```python
from microsoft_agents.hosting.teams import TeamsInfo

# Get team member information
member = await TeamsInfo.get_team_member(context, team_id, user_id)

# Get meeting participant details
participant = await TeamsInfo.get_meeting_participant(
    context, meeting_id, participant_id, tenant_id
)

# Get meeting information
meeting_info = await TeamsInfo.get_meeting_info(context, meeting_id)

# Send message to Teams channel
await TeamsInfo.send_message_to_teams_channel(
    context, activity, channel_id, app_id
)
```

## Messaging Extensions

Handle search and action-based messaging extensions:

```python
class MessagingExtensionAgent(TeamsActivityHandler):
    async def on_teams_messaging_extension_query(
        self, turn_context: TurnContext, query
    ):
        # Handle search queries
        search_term = query.parameters[0].value if query.parameters else ""
        
        results = [
            {
                "type": "result",
                "attachmentLayout": "list",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.thumbnail",
                        "content": {
                            "title": f"Search result for: {search_term}",
                            "text": "Found relevant information",
                            "tap": {
                                "type": "invoke",
                                "value": {"query": search_term}
                            }
                        }
                    }
                ]
            }
        ]
        
        return MessagingExtensionResponse(compose_extension=results[0])
    
    async def on_teams_messaging_extension_submit_action(
        self, turn_context: TurnContext, action
    ):
        # Handle action submissions
        user_input = action.data
        
        # Process the action and return response
        card = {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"Processed: {user_input}"
                }
            ]
        }
        
        return MessagingExtensionActionResponse(
            task={
                "type": "continue",
                "value": {
                    "card": card
                }
            }
        )
```

## Task Modules

Interactive dialogs and forms in Teams:

```python
class TaskModuleAgent(TeamsActivityHandler):
    async def on_teams_task_module_fetch(
        self, turn_context: TurnContext, task_module_request
    ):
        # Show a form to the user
        adaptive_card = {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please enter your information:"
                },
                {
                    "type": "Input.Text",
                    "id": "name",
                    "placeholder": "Your name"
                },
                {
                    "type": "Input.Text",
                    "id": "email",
                    "placeholder": "Your email"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "data": {"action": "submit"}
                }
            ]
        }
        
        return TaskModuleResponse(
            task={
                "type": "continue",
                "value": {
                    "card": adaptive_card,
                    "height": 250,
                    "width": 400,
                    "title": "User Information"
                }
            }
        )
    
    async def on_teams_task_module_submit(
        self, turn_context: TurnContext, task_module_request
    ):
        # Process form submission
        data = task_module_request.data
        name = data.get("name", "")
        email = data.get("email", "")
        
        # Save data and close task module
        await self.save_user_info(name, email)
        
        return TaskModuleResponse(
            task={
                "type": "message",
                "value": f"Thank you {name}! Information saved."
            }
        )
```

## Adaptive Cards & Actions

Handle card interactions and button clicks:

```python
class CardAgent(TeamsActivityHandler):
    async def on_teams_card_action_invoke(self, turn_context: TurnContext):
        # Handle adaptive card button clicks
        action_data = turn_context.activity.value
        action_type = action_data.get("action")
        
        if action_type == "approve":
            await self.handle_approval(turn_context, action_data)
        elif action_type == "reject":
            await self.handle_rejection(turn_context, action_data)
        
        # Return updated card
        updated_card = self.create_updated_card(action_data)
        return InvokeResponse(
            status=200,
            body={
                "task": {
                    "type": "continue",
                    "value": updated_card
                }
            }
        )
    
    def create_approval_card(self, request_id: str):
        return {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Approval Request",
                    "weight": "Bolder"
                },
                {
                    "type": "TextBlock",
                    "text": "Please review and approve this request."
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Approve",
                    "data": {"action": "approve", "requestId": request_id}
                },
                {
                    "type": "Action.Submit",
                    "title": "Reject",
                    "data": {"action": "reject", "requestId": request_id}
                }
            ]
        }
```

## Meeting Integration

Handle Teams meeting events and interactions:

```python
class MeetingAgent(TeamsActivityHandler):
    async def on_teams_meeting_start(
        self, meeting_details, turn_context: TurnContext
    ):
        # Meeting started - send welcome message
        await turn_context.send_activity(
            MessageFactory.text("Meeting started! I'm here to help.")
        )
        
        # Log meeting start
        await self.log_meeting_event("start", meeting_details)
    
    async def on_teams_meeting_participants_join(
        self, participants_event, turn_context: TurnContext
    ):
        # New participants joined
        participant_names = [p.user.name for p in participants_event.members]
        message = f"Welcome {', '.join(participant_names)} to the meeting!"
        
        await turn_context.send_activity(MessageFactory.text(message))
    
    async def on_teams_meeting_participants_leave(
        self, participants_event, turn_context: TurnContext
    ):
        # Participants left
        participant_names = [p.user.name for p in participants_event.members]
        message = f"{', '.join(participant_names)} left the meeting"
        
        await turn_context.send_activity(MessageFactory.text(message))
    
    async def get_meeting_info(self, turn_context: TurnContext):
        # Get current meeting details
        meeting_info = await TeamsInfo.get_meeting_info(turn_context)
        
        return {
            "id": meeting_info.details.id,
            "title": meeting_info.details.title,
            "organizer": meeting_info.organizer.name,
            "start_time": meeting_info.details.scheduled_start_time
        }
```

## File Handling

Handle file uploads and downloads in Teams:

```python
class FileAgent(TeamsActivityHandler):
    async def on_teams_file_consent(
        self, turn_context: TurnContext, file_consent_response
    ):
        if file_consent_response.action == "accept":
            await self.handle_file_upload(turn_context, file_consent_response)
        else:
            await turn_context.send_activity("File upload cancelled")
    
    async def on_teams_file_consent_accept(
        self, turn_context: TurnContext, file_consent_response
    ):
        # File was accepted - handle upload
        file_info = file_consent_response.upload_info
        
        # Upload file content
        with open("local_file.pdf", "rb") as file:
            await self.upload_file_to_teams(file_info.upload_url, file.read())
        
        # Send confirmation
        await turn_context.send_activity(
            MessageFactory.text("File uploaded successfully!")
        )
```

## Configuration & Deployment

### Environment Setup

```python
import os
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.teams import TeamsActivityHandler
from microsoft_agents.authentication.msal import MsalConnectionManager

# Load Teams-specific configuration
teams_config = {
    "TEAMS_APP_ID": os.getenv("TEAMS_APP_ID"),
    "TEAMS_APP_PASSWORD": os.getenv("TEAMS_APP_PASSWORD"),
    "TENANT_ID": os.getenv("TENANT_ID")
}

# Create connection manager
connection_manager = MsalConnectionManager(**teams_config)

# Create adapter
adapter = CloudAdapter(connection_manager=connection_manager)
```

### Teams App Manifest

Your Teams app manifest should include appropriate permissions:

```json
{
    "manifestVersion": "1.16",
    "version": "1.0.0",
    "id": "your-app-id",
    "bots": [
        {
            "botId": "your-bot-id",
            "scopes": ["personal", "team", "groupchat"],
            "commandLists": [
                {
                    "scopes": ["personal", "team", "groupchat"],
                    "commands": [
                        {
                            "title": "Help",
                            "description": "Get help with the agent"
                        }
                    ]
                }
            ]
        }
    ],
    "composeExtensions": [
        {
            "botId": "your-bot-id",
            "commands": [
                {
                    "id": "search",
                    "type": "query",
                    "title": "Search",
                    "description": "Search for information",
                    "parameters": [
                        {
                            "name": "searchKeyword",
                            "title": "Search",
                            "description": "Enter search term"
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Advanced Patterns

### Multi-Feature Teams Agent

```python
class ComprehensiveTeamsAgent(TeamsActivityHandler):
    def __init__(self):
        super().__init__()
        self.commands = {
            "help": self.show_help,
            "team": self.show_team_info,
            "search": self.handle_search,
            "approve": self.show_approval_card
        }
    
    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.lower().strip()
        
        # Handle command-based interactions
        for command, handler in self.commands.items():
            if command in text:
                await handler(turn_context)
                return
        
        # Default response
        await turn_context.send_activity("Try 'help' for available commands")
    
    async def show_help(self, turn_context: TurnContext):
        help_card = MessageFactory.attachment(
            self.create_help_card()
        )
        await turn_context.send_activity(help_card)
    
    async def show_team_info(self, turn_context: TurnContext):
        team_id = turn_context.activity.channel_data.get("team", {}).get("id")
        if team_id:
            members = await TeamsInfo.get_team_members(turn_context, team_id)
            member_list = "\n".join([f"- {m.name}" for m in members])
            await turn_context.send_activity(f"Team members:\n{member_list}")
        else:
            await turn_context.send_activity("This command works only in team channels")
```

### Error Handling

```python
class RobustTeamsAgent(TeamsActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        try:
            await self.process_message(turn_context)
        except Exception as e:
            await self.handle_error(turn_context, e)
    
    async def handle_error(self, turn_context: TurnContext, error: Exception):
        error_message = "Sorry, something went wrong. Please try again."
        
        if "not found" in str(error).lower():
            error_message = "The requested resource was not found."
        elif "permission" in str(error).lower():
            error_message = "You don't have permission for this action."
        
        await turn_context.send_activity(MessageFactory.text(error_message))
```

## Testing Teams Agents

### Unit Testing

```python
import pytest
from microsoft_agents.hosting.teams import TeamsActivityHandler
from microsoft_agents.activity import Activity, ChannelAccount

@pytest.mark.asyncio
async def test_teams_member_added():
    agent = MyTeamsAgent()
    
    # Create Teams member added activity
    activity = Activity(
        type="conversationUpdate",
        channel_id="msteams",
        members_added=[ChannelAccount(id="user123", name="John Doe")],
        recipient=ChannelAccount(id="bot456", name="Test Bot"),
        channel_data={"team": {"id": "team789"}}
    )
    
    context = create_test_context(activity)
    await agent.on_conversation_update_activity(context)
    
    # Verify welcome message was sent
    assert len(context.sent_activities) == 1
    assert "welcome" in context.sent_activities[0].text.lower()
```

## Key Classes Reference

- **`TeamsActivityHandler`** - Main handler class with Teams-specific event methods
- **`TeamsInfo`** - Utility class for Teams operations (members, meetings, channels)
- **`MessagingExtensionQuery/Response`** - Handle search and messaging extensions
- **`TaskModuleRequest/Response`** - Interactive dialogs and forms
- **`TabRequest/Response`** - Tab application interactions

## Features Supported

✅ **Messaging Extensions** - Search and action-based extensions  
✅ **Task Modules** - Interactive dialogs and forms  
✅ **Adaptive Cards** - Rich card interactions  
✅ **Meeting Events** - Start, end, participant changes  
✅ **Team Management** - Member operations, channel messaging  
✅ **File Handling** - Upload/download with consent flow  
✅ **Tab Apps** - Personal and team tab interactions  
✅ **Proactive Messaging** - Send messages to channels/users  

## Migration from Bot Framework

| Bot Framework Teams | Microsoft Agents Teams |
|-------------------|------------------------|
| `TeamsActivityHandler` | `TeamsActivityHandler` |
| `TeamsInfo` | `TeamsInfo` |
| `on_teams_members_added` | `on_teams_members_added_activity` |
| `MessagingExtensionQuery` | `MessagingExtensionQuery` |
| `TaskModuleRequest` | `TaskModuleRequest` |

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
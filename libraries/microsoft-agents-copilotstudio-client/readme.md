# Microsoft Agents Copilot Studio Client

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/)

The Copilot Studio Client is for connecting to and interacting with agents created in Microsoft Copilot Studio. This library allows you to integrate Copilot Studio agents into your Python applications.

This client library provides a direct connection to Copilot Studio agents, bypassing traditional chat channels. It's perfect for integrating AI conversations into your applications, building custom UIs, or creating agent-to-agent communication flows.

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
pip install microsoft-agents-copilotstudio-client
```

## Quick Start

### Basic Setup

#### Standard Environment-Based Connection

Code below from the [main.py in the Copilot Studio Client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/src/main.py)
```python
def create_client():
    settings = ConnectionSettings(
        environment_id=environ.get("COPILOTSTUDIOAGENT__ENVIRONMENTID"),
        agent_identifier=environ.get("COPILOTSTUDIOAGENT__SCHEMANAME"),
        cloud=None,
        copilot_agent_type=None,
        custom_power_platform_cloud=None,
    )
    token = acquire_token(
        settings,
        app_client_id=environ.get("COPILOTSTUDIOAGENT__AGENTAPPID"),
        tenant_id=environ.get("COPILOTSTUDIOAGENT__TENANTID"),
    )
    copilot_client = CopilotClient(settings, token)
    return copilot_client
```

#### DirectConnect URL Mode (Simplified Setup)

For simplified setup, you can use a DirectConnect URL instead of environment-based configuration:

```python
def create_client_direct():
    settings = ConnectionSettings(
        environment_id="",  # Not needed with DirectConnect URL
        agent_identifier="",  # Not needed with DirectConnect URL
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/your-bot-id"
    )
    token = acquire_token(...)
    copilot_client = CopilotClient(settings, token)
    return copilot_client
```

#### Advanced Configuration Options

```python
settings = ConnectionSettings(
    environment_id="your-env-id",
    agent_identifier="your-agent-id",
    cloud=PowerPlatformCloud.PROD,
    copilot_agent_type=AgentType.PUBLISHED,
    custom_power_platform_cloud=None,
    direct_connect_url=None,  # Optional: Direct URL to agent
    use_experimental_endpoint=False,  # Optional: Enable experimental features
    enable_diagnostics=False,  # Optional: Enable diagnostic logging (logs HTTP details)
    client_session_settings={"timeout": aiohttp.ClientTimeout(total=60)}  # Optional: aiohttp settings
)
```

**Diagnostic Logging Details**:
When `enable_diagnostics=True`, the CopilotClient logs detailed HTTP communication using Python's `logging` module at the `DEBUG` level:
- Pre-request: Logs the full request URL (`>>> SEND TO {url}`)
- Post-response: Logs all HTTP response headers in a formatted table
- Errors: Logs error messages with status codes

To see diagnostic output, configure your Python logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Experimental Endpoint Details**:
When `use_experimental_endpoint=True`, the CopilotClient will automatically capture and use the experimental endpoint URL from the first response:
- The server returns the experimental endpoint in the `x-ms-d2e-experimental` response header
- Once captured, this URL is stored in `settings.direct_connect_url` and used for all subsequent requests
- This feature is only active when `use_experimental_endpoint=True` AND `direct_connect_url` is not already set
- The experimental endpoint allows access to pre-release features and optimizations

### Start a Conversation

#### Simple Start

The code below is summarized from the [main.py in the Copilot Studio Client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/src/main.py). See that sample for complete & working code.

```python
copilot_client = create_client()
async for activity in copilot_client.start_conversation(emit_start_conversation_event=True):
    if activity.type == ActivityTypes.message:
        print(f"\n{activity.text}")

# Ask questions
async for reply in copilot_client.ask_question("Who are you?", conversation_id):
    if reply.type == ActivityTypes.message:
        print(f"\n{reply.text}")
```

#### Start with Advanced Options (Locale Support)

```python
from microsoft_agents.copilotstudio.client import StartRequest

# Create a start request with locale
start_request = StartRequest(
    emit_start_conversation_event=True,
    locale="en-US",  # Optional: specify conversation locale
    conversation_id="custom-conv-id"  # Optional: provide your own conversation ID
)

async for activity in copilot_client.start_conversation_with_request(start_request):
    if activity.type == ActivityTypes.message:
        print(f"\n{activity.text}")
```

### Send Activities

#### Send a Custom Activity

```python
from microsoft_agents.activity import Activity

activity = Activity(
    type="message",
    text="Hello, agent!",
    conversation={"id": conversation_id}
)

async for reply in copilot_client.send_activity(activity):
    print(f"Response: {reply.text}")
```

#### Execute with Explicit Conversation ID

```python
# Execute an activity with a specific conversation ID
activity = Activity(type="message", text="What's the weather?")

async for reply in copilot_client.execute(conversation_id="conv-123", activity=activity):
    print(f"Response: {reply.text}")
```

### Subscribe to Conversation Events

For real-time event streaming with resumption support:

```python
from microsoft_agents.copilotstudio.client import SubscribeEvent

# Subscribe to conversation events
async for subscribe_event in copilot_client.subscribe(
    conversation_id="conv-123",
    last_received_event_id=None  # Optional: resume from last event
):
    activity = subscribe_event.activity
    event_id = subscribe_event.event_id  # Use for resumption

    if activity.type == ActivityTypes.message:
        print(f"[{event_id}] {activity.text}")
```

### Environment Variables

Set up your `.env` file with the following options:

#### Standard Environment-Based Configuration

```bash
# Required (unless using DIRECT_CONNECT_URL)
ENVIRONMENT_ID=your-power-platform-environment-id
AGENT_IDENTIFIER=your-copilot-studio-agent-id
APP_CLIENT_ID=your-azure-app-client-id
TENANT_ID=your-azure-tenant-id

# Optional Cloud Configuration
CLOUD=PROD  # Options: PROD, GOV, HIGH, DOD, MOONCAKE, DEV, TEST, etc.
COPILOT_AGENT_TYPE=PUBLISHED  # Options: PUBLISHED, PREBUILT
CUSTOM_POWER_PLATFORM_CLOUD=https://custom.cloud.com
```

#### DirectConnect URL Configuration (Alternative)

```bash
# Required for DirectConnect mode
DIRECT_CONNECT_URL=https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/your-bot-id
APP_CLIENT_ID=your-azure-app-client-id
TENANT_ID=your-azure-tenant-id

# Optional
CLOUD=PROD  # Used for token audience resolution
```

#### Advanced Options

```bash
# Experimental and diagnostic features
USE_EXPERIMENTAL_ENDPOINT=false  # Enable automatic experimental endpoint capture
ENABLE_DIAGNOSTICS=false  # Enable diagnostic logging (logs HTTP requests/responses)
```

**Experimental Endpoint**: When `USE_EXPERIMENTAL_ENDPOINT=true`, the client automatically captures and uses the experimental endpoint URL from the server's `x-ms-d2e-experimental` response header. This feature:
- Only activates when `direct_connect_url` is not already set
- Captures the URL from the first response and stores it for all subsequent requests
- Provides access to pre-release features and performance optimizations
- Useful for testing new capabilities before general availability

**Diagnostic Logging**: When `ENABLE_DIAGNOSTICS=true` or `enable_diagnostics=True`, the client will log detailed HTTP request and response information including:
- Request URLs before sending
- All response headers with their values
- Error messages for failed requests

This is useful for debugging connection issues, authentication problems, or understanding the communication flow with Copilot Studio. Diagnostic logs use Python's standard `logging` module at the `DEBUG` level.

#### Using Environment Variables in Code

The `ConnectionSettings.populate_from_environment()` helper method automatically loads these variables:

```python
from microsoft_agents.copilotstudio.client import ConnectionSettings

# Automatically loads from environment variables
settings_dict = ConnectionSettings.populate_from_environment()
settings = ConnectionSettings(**settings_dict)
```

## Features

### Core Capabilities

✅ **Real-time streaming** - Server-sent events for live responses
✅ **Multi-cloud support** - Works across all Power Platform clouds (PROD, GOV, HIGH, DOD, MOONCAKE, etc.)
✅ **Rich content** - Support for cards, actions, and attachments
✅ **Conversation management** - Maintain context across interactions
✅ **Custom activities** - Send structured data to agents
✅ **Async/await** - Modern Python async support

### Advanced Features

✅ **DirectConnect URLs** - Simplified connection with direct bot URLs
✅ **Locale support** - Specify conversation language with `StartRequest`
✅ **Event subscription** - Subscribe to conversation events with SSE resumption
✅ **Multiple connection modes** - Environment-based or DirectConnect URL
✅ **Token audience resolution** - Automatic cloud detection from URLs
✅ **User-Agent tracking** - Automatic SDK version and platform headers
✅ **Environment configuration** - Automatic loading from environment variables
✅ **Experimental endpoints** - Toggle experimental API features
✅ **Diagnostic logging** - HTTP request/response logging for debugging and troubleshooting

### API Methods

| Method | Description |
|--------|-------------|
| `start_conversation()` | Start a new conversation with basic options |
| `start_conversation_with_request()` | Start with advanced options (locale, custom conversation ID) |
| `ask_question()` | Send a text question to the agent |
| `ask_question_with_activity()` | Send a custom Activity object |
| `send_activity()` | Send any activity (alias for ask_question_with_activity) |
| `execute()` | Execute an activity with explicit conversation ID |
| `subscribe()` | Subscribe to conversation events with resumption support |

### Configuration Models

| Class | Description |
|-------|-------------|
| `ConnectionSettings` | Main configuration class with all connection options |
| `StartRequest` | Advanced start options (locale, conversation ID) |
| `SubscribeEvent` | Event wrapper with activity and SSE event ID |
| `PowerPlatformCloud` | Enum for cloud environments |
| `AgentType` | Enum for agent types (PUBLISHED, PREBUILT) |
| `UserAgentHelper` | Utility for generating user-agent headers |

## Connection Modes

The client supports two connection modes:

### 1. Environment-Based Connection (Standard)

Uses environment ID and agent identifier to construct the connection URL:

```python
settings = ConnectionSettings(
    environment_id="aaaabbbb-1111-2222-3333-ccccddddeeee",
    agent_identifier="cr123_myagent"
)
```

**URL Pattern:**
`https://{env-prefix}.{env-suffix}.environment.api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/{agent-id}/conversations`

### 2. DirectConnect URL Mode (Simplified)

Uses a direct URL to the agent, bypassing environment resolution:

```python
settings = ConnectionSettings(
    environment_id="",
    agent_identifier="",
    direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/cr123_myagent"
)
```

**Benefits:**
- Simpler configuration with single URL
- Automatic cloud detection for token audience
- Works across environments without environment ID lookup
- Useful for multi-tenant scenarios

## Token Audience Resolution

The client automatically determines the correct token audience:

```python
# For environment-based connections
audience = PowerPlatformEnvironment.get_token_audience(settings)
# Returns: https://api.powerplatform.com/.default

# For DirectConnect URLs
audience = PowerPlatformEnvironment.get_token_audience(
    settings=ConnectionSettings("", "", direct_connect_url="https://api.gov.powerplatform.microsoft.us/...")
)
# Returns: https://api.gov.powerplatform.microsoft.us/.default
```

## Troubleshooting

### Common Issues

**Authentication failed**
- Verify your app is registered in Azure AD
- Check that token has the correct audience scope (use `PowerPlatformEnvironment.get_token_audience()`)
- Ensure your app has permissions to the Power Platform environment
- For DirectConnect URLs, verify cloud setting matches the URL domain

**Agent not found**
- Verify the environment ID and agent identifier
- Check that the agent is published and accessible
- Confirm you're using the correct cloud setting
- For DirectConnect URLs, ensure the URL is correct and complete

**Connection timeout**
- Check network connectivity to Power Platform
- Verify firewall settings allow HTTPS traffic
- Try a different cloud region if available
- Check if `client_session_settings` timeout is appropriate

**Invalid DirectConnect URL**
- Ensure URL includes scheme (https://)
- Verify URL format matches expected pattern
- Check for trailing slashes (automatically normalized)
- Confirm URL points to the correct cloud environment

## Requirements

- Python 3.10+ (supports 3.10, 3.11, 3.12, 3.13, 3.14)
- Valid Azure AD app registration
- Access to Microsoft Power Platform environment
- Published Copilot Studio agent

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
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
pip install microsoft-agents-copilotstudio-client
```

## Quick Start

### Basic Setup

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

### Start a Conversation
The code below is summarized from the [main.py in the Copilot Studio Client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/src/main.py). See that sample for complete & working code. 

```python
    copilot_client = create_client()
    act = copilot_client.start_conversation(True)

    ...

    replies = copilot_client.ask_question("Who are you?", conversation_id)
    async for reply in replies:
        if reply.type == ActivityTypes.message:
            print(f"\n{reply.text}")
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
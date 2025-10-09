# Microsoft Agents MSAL Authentication

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/)

Provides secure authentication for your agents using Microsoft Authentication Library (MSAL). It handles getting tokens from Azure AD so your agent can securely communicate with Microsoft services like Teams, Graph API, and other Azure resources.

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
pip install microsoft-agents-authentication-msal
```

## Quick Start

### Basic Setup with Client Secret

```python
from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core import AgentAuthConfiguration, AuthTypes

# Configure authentication
config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.client_secret,
    TENANT_ID="your-tenant-id",
    CLIENT_ID="your-client-id", 
    CLIENT_SECRET="your-client-secret"
)

# Create auth provider
auth = MsalAuth(config)

# Get access token
token = await auth.get_access_token(
    resource_url="https://graph.microsoft.com",
    scopes=["https://graph.microsoft.com/.default"]
)
```

### Using with Connection Manager

```python
from microsoft_agents.authentication.msal import MsalConnectionManager

# Load from environment variables
connection_manager = MsalConnectionManager(**agents_sdk_config)

# Use with hosting adapter
from microsoft_agents.hosting.aiohttp import CloudAdapter
adapter = CloudAdapter(connection_manager=connection_manager)
```

## Authentication Types

### 1. Client Secret (Most Common)
```python
config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.client_secret,
    TENANT_ID="your-tenant-id",
    CLIENT_ID="your-app-id",
    CLIENT_SECRET="your-secret"
)
```

### 2. Certificate-based
```python
config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.client_certificate,
    TENANT_ID="your-tenant-id", 
    CLIENT_ID="your-app-id",
    CLIENT_CERTIFICATE_PATH="/path/to/cert.pem",
    CLIENT_CERTIFICATE_PRIVATE_KEY_PATH="/path/to/key.pem"
)
```

### 3. Managed Identity (Azure hosting)
```python
# System-assigned managed identity
config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.system_managed_identity
)

# User-assigned managed identity  
config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.user_managed_identity,
    CLIENT_ID="managed-identity-client-id"
)
```

## Environment Configuration

Set up your `.env` file:

```bash
# Basic authentication
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-client-secret

# Multiple connections
CONNECTIONS__GRAPH__SETTINGS__TENANTID=your-tenant-id
CONNECTIONS__GRAPH__SETTINGS__CLIENTID=your-graph-app-id
CONNECTIONS__GRAPH__SETTINGS__CLIENTSECRET=your-graph-secret
```

Load configuration:
```python
from microsoft_agents.activity import load_configuration_from_env
from os import environ

agents_sdk_config = load_configuration_from_env(environ)
connection_manager = MsalConnectionManager(**agents_sdk_config)
```

## Advanced Features

### On-Behalf-Of (OBO) Flow
```python
# Get token on behalf of user
user_token = await auth.acquire_token_on_behalf_of(
    scopes=["https://graph.microsoft.com/User.Read"],
    user_assertion="user-jwt-token"
)
```

### Agentic Authentication
```python
# For multi-agent scenarios
app_token = await auth.get_agentic_application_token("agent-instance-id")
user_token = await auth.get_agentic_user_token(
    "agent-instance-id", 
    "user@company.com", 
    ["User.Read"]
)
```

### Connection Mapping
```python
# Map different connections to different services
connection_manager = MsalConnectionManager(
    connections_map=[
        {"CONNECTION": "GRAPH", "SERVICEURL": "graph.microsoft.com"},
        {"CONNECTION": "TEAMS", "SERVICEURL": "teams.microsoft.com"}
    ]
)
```

## Common Use Cases

### Teams Agent
```python
from microsoft_agents.hosting.aiohttp import CloudAdapter

CONFIG = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.client_secret,
    TENANT_ID=environ.get("TENANT_ID"),
    CLIENT_ID=environ.get("CLIENT_ID"), 
    CLIENT_SECRET=environ.get("CLIENT_SECRET")
)

connection_manager = MsalConnectionManager(
    connections_configurations={"SERVICE_CONNECTION": CONFIG}
)

adapter = CloudAdapter(connection_manager=connection_manager)
```

### Graph API Access
```python
# Configure for Microsoft Graph
graph_config = AgentAuthConfiguration(
    AUTH_TYPE=AuthTypes.client_secret,
    TENANT_ID="your-tenant-id",
    CLIENT_ID="your-app-id",
    CLIENT_SECRET="your-secret",
    SCOPES=["https://graph.microsoft.com/.default"]
)

auth = MsalAuth(graph_config)
token = await auth.get_access_token("https://graph.microsoft.com")
```

## Key Classes

- **`MsalAuth`** - Core authentication provider using MSAL
- **`MsalConnectionManager`** - Manages multiple authentication connections
- **`AgentAuthConfiguration`** - Configuration settings for auth providers

## Features

✅ **Multiple auth types** - Client secret, certificate, managed identity  
✅ **Token caching** - Automatic token refresh and caching  
✅ **Multi-tenant** - Support for different Azure AD tenants  
✅ **Agent-to-agent** - Secure communication between agents  
✅ **On-behalf-of** - Act on behalf of users  
✅ **Scope resolution** - Dynamic scope handling with placeholders

## Troubleshooting

### Common Issues

**Token acquisition failed**
- Verify your client ID, secret, and tenant ID
- Check that your app has the required permissions
- Ensure scopes are correctly formatted

**Managed Identity not working**
- Verify you're running on Azure with managed identity enabled
- Check that the identity has required permissions

## Security Best Practices

- Store secrets in Azure Key Vault or environment variables
- Use managed identities when possible (no secrets to manage)
- Regularly rotate client secrets and certificates
- Use least-privilege principle for scopes and permissions

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
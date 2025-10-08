# Microsoft Agents MSAL Authentication

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/)

MSAL-based authentication library for Microsoft 365 Agents SDK. Handles Azure AD authentication with support for client secrets, certificates, and managed identities.

## What is this?

This library provides secure authentication for your agents using Microsoft Authentication Library (MSAL). It handles getting tokens from Azure AD so your agent can securely communicate with Microsoft services like Teams, Graph API, and other Azure resources.

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

## Need Help?

- 📖 [Full SDK Documentation](https://aka.ms/agents)
- 🔐 [Azure AD App Registration Guide](https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.
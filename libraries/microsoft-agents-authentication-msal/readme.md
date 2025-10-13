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

Define your client secrets in the ENV file
```python
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=client-secret
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=tenant-id
```

Load the Configuration (Code from [main.py Quickstart Sample](https://github.com/microsoft/Agents/blob/main/samples/python/quickstart/src/main.py))

```python
from .start_server import start_server

start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
```
Then start the Agent (code snipped from (start_server.py Quickstart Sample](https://github.com/microsoft/Agents/blob/main/samples/python/quickstart/src/start_server.py)):

```python
def start_server(
    agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
    async def entry_point(req: Request) -> Response:
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(
            req,
            agent,
            adapter,
        )
[...]
```

## Authentication Types
The M365 Agents SDK in Python supports the following Auth types:
```python
class AuthTypes(str, Enum):
    certificate = "certificate"
    certificate_subject_name = "CertificateSubjectName"
    client_secret = "ClientSecret"
    user_managed_identity = "UserManagedIdentity"
    system_managed_identity = "SystemManagedIdentity"
```

## Key Classes

- **`MsalAuth`** - Core authentication provider using MSAL
- **`MsalConnectionManager`** - Manages multiple authentication connections

## Features

✅ **Multiple auth types** - Client secret, certificate, managed identity  
✅ **Token caching** - Automatic token refresh and caching  
✅ **Multi-tenant** - Support for different Azure AD tenants  
✅ **Agent-to-agent** - Secure communication between agents  
✅ **On-behalf-of** - Act on behalf of users  

# Security Best Practices

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

w
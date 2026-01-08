# Authentication Guide

Handle Azure Bot Service authentication in your tests.

## Overview

The framework handles OAuth authentication for Azure Bot Service credentials automatically.

## Configuration

### Setup Environment Variables

Create `.env` file:

```env
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=<your-app-id>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=<your-tenant-id>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=<your-secret>
```

## Getting Credentials

### From Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Bot Service"
3. Select your bot
4. Go to "Configuration"
5. Click "Manage password"
6. Create or view your secret
7. Copy App ID, Tenant ID, and Secret to `.env`

### From Azure CLI

```bash
# Login
az login

# List apps
az ad app list --display-name "MyAgent"

# Get details
az ad app show --id <app-id>
```

## Token Generation

### Generate Token Programmatically

```python
from microsoft_agents.testing import generate_token

token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant-id"
)

print(f"Token: {token}")
```

### Generate from Config

```python
from microsoft_agents.testing import SDKConfig, generate_token_from_config

config = SDKConfig(env_path=".env")
token = generate_token_from_config(config)
```

## Using Auth in Tests

### Automatic Authentication

The `Integration` class handles authentication automatically:

```python
from microsoft_agents.testing import Integration

class TestWithAuth(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_authenticated(self, agent_client):
        # agent_client already authenticated
        await agent_client.send_activity("Test")
```

## Local Auth Server

### Run Auth Server

```bash
aclip --env_path .env auth --port 3978
```

### Use in Development

```bash
# Terminal 1: Start auth server
aclip --env_path .env auth --port 3978 &

# Terminal 2: Run tests
pytest tests/ -v
```

## Troubleshooting Auth

### Issue: Invalid Credentials

```
Error: Invalid credentials
```

**Solution**:
```bash
# Verify credentials in .env
cat .env

# Verify with Azure CLI
az ad app show --id <app-id>
```

### Issue: Token Expired

The framework automatically refreshes tokens. If issues persist:

```python
from microsoft_agents.testing import AgentClient

# Recreate client to refresh token
client = AgentClient(
    agent_url="http://localhost:3978/",
    client_id="your-id",
    client_secret="your-secret",
    tenant_id="your-tenant",
    service_url="http://localhost:8001/"
)
```

### Issue: Unauthorized Error

```
Error: 401 Unauthorized
```

**Solution**:
1. Check credentials in `.env`
2. Verify bot service is configured
3. Ensure app has correct permissions

---

**Related Guides**:
- [Installation](./INSTALLATION.md)
- [Quick Start](./QUICK_START.md)

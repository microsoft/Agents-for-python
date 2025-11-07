# Microsoft 365 Agents SDK for Python - Testing Framework

[![PyPI](https://img.shields.io/pypi/v/microsoft-agents-testing)](https://pypi.org/project/microsoft-agents-testing/)

A comprehensive testing framework designed specifically for Microsoft 365 Agents SDK, providing essential utilities and abstractions to streamline integration testing, authentication, and end-to-end agent validation.

## Why This Package Exists

Building and testing conversational agents presents unique challenges that standard testing frameworks don't address. This package eliminates these pain points by providing useful abstractions specifically designed for agent testing scenarios.

## Key Features

### 🔐 Authentication Utilities
- **OAuth2 Token Generation**: Generate access tokens using client credentials flow
- **Configuration-Based Auth**: Load credentials from environment variables or config objects
- **MSAL Integration**: Built-in support for Microsoft Authentication Library

```python
from microsoft_agents.testing import generate_token, generate_token_from_config

# Generate token directly
token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant"
)

# Or from SDK config
token = generate_token_from_config(sdk_config)
```

### 🧪 Integration Test Framework
- **Pytest Fixtures**: Pre-built fixtures for common test scenarios
- **Environment Abstraction**: Reusable environment setup for different hosting configurations
- **Sample Management**: Base classes for organizing test samples and configurations
- **Application Runners**: Abstract server lifecycle management for integration tests

```python
from microsoft_agents.testing import Integration, Environment, Sample

class MyAgentTests(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, agent_client, sample):
        # Client and sample are automatically set up via fixtures
        response = await agent_client.send_activity("Hello")
        assert response is not None
```

### 🤖 Agent Communication Clients
- **AgentClient**: High-level client for sending Activities to agents
- **ResponseClient**: Handle responses from agent services
- **Automatic Token Management**: Clients handle authentication automatically
- **Delivery Mode Support**: Test both standard and `ExpectReplies` delivery patterns

```python
from microsoft_agents.testing import AgentClient

client = AgentClient(
    agent_url="http://localhost:3978",
    cid="conversation-id",
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    client_secret="your-secret"
)

# Send simple text message
response = await client.send_activity("What's the weather?")

# Send Activity with ExpectReplies
replies = await client.send_expect_replies(
    Activity(type=ActivityTypes.message, text="Hello")
)
```

### 🛠️ Testing Utilities
- **Activity Population**: Automatically fill default Activity properties for testing
- **URL Parsing**: Extract host and port from service URLs
- **Configuration Management**: Centralized SDK configuration for tests

```python
from microsoft_agents.testing import populate_activity, get_host_and_port

# Populate test activity with defaults
activity = populate_activity(
    Activity(text="Hello"),
    defaults={"service_url": "http://localhost", "channel_id": "test"}
)

# Parse service URLs
host, port = get_host_and_port("http://localhost:3978/api/messages")
```

## Who Should Use This Package

- **Agent Developers**: Testing agents built with `microsoft-agents-hosting-core` and related packages
- **QA Engineers**: Writing integration and E2E tests for conversational AI systems
- **DevOps Teams**: Automating agent validation in CI/CD pipelines
- **Sample Authors**: Creating reproducible examples and documentation

## Integration with CI/CD

This package is designed for seamless integration into continuous integration pipelines:

```yaml
# Example: GitHub Actions
- name: Run Agent Integration Tests
  run: |
    pip install microsoft-agents-testing pytest pytest-asyncio
    pytest tests/integration/ -v
  env:
    CLIENT_ID: ${{ secrets.AGENT_CLIENT_ID }}
    CLIENT_SECRET: ${{ secrets.AGENT_CLIENT_SECRET }}
    TENANT_ID: ${{ secrets.TENANT_ID }}
```

## Quick Start Example

```python
import pytest
from microsoft_agents.testing import Integration, AiohttpEnvironment, Sample
from microsoft_agents.activity import Activity

class MyAgentSample(Sample):
    async def init_app(self):
        # Initialize your agent application
        self.app = create_my_agent_app(self.env)
    
    @classmethod
    async def get_config(cls):
        return {"service_url": "http://localhost:3978"}

class TestMyAgent(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    
    _agent_url = "http://localhost:3978"
    _cid = "test-conversation"
    
    @pytest.mark.asyncio
    async def test_greeting(self, agent_client):
        response = await agent_client.send_activity("Hello")
        assert "Hi there" in response
    
    @pytest.mark.asyncio
    async def test_conversation(self, agent_client):
        replies = await agent_client.send_expect_replies("What can you do?")
        assert len(replies) > 0
        assert replies[0].type == "message"
```

## Related Packages

This package complements the Microsoft 365 Agents SDK ecosystem:

- `microsoft-agents-activity`: Activity types and protocols
- `microsoft-agents-hosting-core`: Core hosting framework
- `microsoft-agents-hosting-aiohttp`: aiohttp hosting integration
- `microsoft-agents-authentication-msal`: MSAL authentication

## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA). For details, visit [https://cla.opensource.microsoft.com](https://cla.opensource.microsoft.com).

## License

MIT

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/microsoft/Agents-for-python).

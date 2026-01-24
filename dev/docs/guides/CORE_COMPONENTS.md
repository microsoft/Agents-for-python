# Core Components Guide

Understand the fundamental building blocks of the Microsoft Agents Testing Framework.

## Component Overview

The framework is built on several core components that work together:

```
┌─────────────────────────────────────────────────┐
│         Integration Base Class                   │
│  (Main entry point for writing tests)            │
└─────────────────────────────────────────────────┘
  ├─ AgentClient           (Send activities)
  ├─ ResponseClient        (Receive responses)
  ├─ Environment           (Setup & teardown)
  └─ Sample                (Your agent app)
```

## 1. Integration Class

The `Integration` class is your starting point for writing integration tests.

### Purpose
- Base class for all integration test classes
- Provides pytest fixtures
- Manages test lifecycle
- Integrates with Environment and Sample

### Basic Usage

```python
from microsoft_agents.testing import Integration

class TestMyAgent(Integration):
    # Configuration
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    # Optional: custom environment
    _environment_cls = MyCustomEnvironment
    _sample_cls = MyCustomSample
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `service_url` | `str` | URL of response mock service |
| `agent_url` | `str` | URL of your agent |
| `config` | `SDKConfig` | Loaded configuration |

### Key Methods

| Method | Purpose |
|--------|---------|
| `setup_method()` | Initialize test (called before each test) |
| `create_agent_client()` | Create AgentClient instance |

### Available Fixtures

Test methods receive these fixtures automatically:

```python
@pytest.mark.asyncio
async def test_something(
    self,
    environment: Environment,           # Test environment
    sample: Sample,                     # Your agent app
    agent_client: AgentClient,          # Send activities
    response_client: ResponseClient     # Receive responses
):
    pass
```

## 2. AgentClient

The `AgentClient` sends activities (messages) to your agent and handles responses.

### Purpose
- Send activities to agent
- Handle authentication
- Manage conversation state
- Support different activity types

### Constructor

```python
from microsoft_agents.testing import AgentClient

client = AgentClient(
    agent_url="http://localhost:3978/",
    cid="conversation-123",                    # Conversation ID
    client_id="your-app-id",                   # Azure AD app ID
    tenant_id="your-tenant-id",                # Azure tenant ID
    client_secret="your-secret",               # Azure secret
    service_url="http://localhost:8001/",      # Response service URL
    default_activity_data=None,                # Default activity fields
    default_sleep=0.5                          # Default sleep duration
)
```

### Key Methods

#### `send_activity()`
Send a simple text message:

```python
# Simple text
await client.send_activity("Hello agent!")

# With custom sleep
await client.send_activity("Question?", sleep=1.0)

# Send Activity object
from microsoft_agents.activity import Activity

activity = Activity(
    type="message",
    text="Hello!",
    channelId="directline"
)
await client.send_activity(activity)
```

#### `send_expect_replies()`
Send activity and wait for replies:

```python
from microsoft_agents.activity import Activity

activity = Activity(type="message", text="Hello?")
replies = await client.send_expect_replies(activity)

for reply in replies:
    print(f"Reply: {reply.text}")
```

#### `send_invoke_activity()`
Send invoke activity:

```python
activity = Activity(
    type="invoke",
    name="custom_action",
    value={"key": "data"}
)
result = await client.send_invoke_activity(activity)
```

#### `close()`
Close the client session:

```python
await client.close()
```

### Usage Example

```python
@pytest.mark.asyncio
async def test_conversation(self, agent_client: AgentClient):
    # Send message
    await agent_client.send_activity("Hi there!")
    
    # Send question
    await agent_client.send_activity("How are you?", sleep=1.0)
    
    # Clean up
    await agent_client.close()
```

## 3. ResponseClient

The `ResponseClient` receives and retrieves responses from your agent.

### Purpose
- Mock response service
- Collect activities from agent
- Provide response retrieval methods
- Support async context manager

### Constructor

```python
from microsoft_agents.testing import ResponseClient

client = ResponseClient(
    host="localhost",           # Host address
    port=9873,                  # Port number
    cid="conversation-123"      # Conversation ID
)
```

### Key Methods

#### `pop()`
Retrieve and clear activities:

```python
# Get all received activities
activities = await response_client.pop()

# Iterate through responses
for activity in activities:
    print(f"Text: {activity.text}")
    print(f"Type: {activity.type}")
```

#### Async Context Manager

```python
async with ResponseClient() as client:
    # Use client
    activities = await client.pop()
```

### Usage Pattern

```python
@pytest.mark.asyncio
async def test_response(self, agent_client, response_client):
    # Send activity
    await agent_client.send_activity("Test")
    
    # Wait for response
    await asyncio.sleep(0.5)  # Give agent time to respond
    
    # Get responses
    responses = await response_client.pop()
    
    # Assertions
    assert len(responses) > 0
    assert responses[0].text is not None
```

## 4. Environment

The `Environment` manages test setup and teardown.

### Purpose
- Initialize test environment
- Setup/teardown resources
- Create application runner
- Manage environment variables

### Base Interface

```python
from microsoft_agents.testing import Environment
from abc import ABC, abstractmethod

class Environment(ABC):
    @abstractmethod
    async def init_env(self, environ_config: dict) -> None:
        """Initialize environment"""
        pass
    
    @abstractmethod
    def create_runner(self, *args, **kwargs):
        """Create application runner"""
        pass
```

### Built-in: AiohttpEnvironment

For aiohttp-based agents:

```python
from microsoft_agents.testing import AiohttpEnvironment

class MyTest(Integration):
    _environment_cls = AiohttpEnvironment
```

### Custom Environment

```python
from microsoft_agents.testing import Environment
from aiohttp import web

class CustomEnvironment(Environment):
    def __init__(self):
        self.app = None
        self.runner = None
    
    async def init_env(self, environ_config: dict):
        """Setup environment"""
        self.app = web.Application()
        # Configure app
    
    def create_runner(self, *args, **kwargs):
        """Create runner"""
        return web.AppRunner(self.app)
```

## 5. Sample

The `Sample` represents your agent application.

### Purpose
- Define agent application
- Provide configuration
- Initialize application
- Manage application lifecycle

### Base Interface

```python
from microsoft_agents.testing import Sample
from abc import abstractmethod

class Sample(ABC):
    def __init__(self, environment: Environment, **kwargs):
        self.environment = environment
    
    @classmethod
    async def get_config(cls) -> dict:
        """Get application configuration"""
        pass
    
    @abstractmethod
    async def init_app(self):
        """Initialize application"""
        pass
```

### Minimal Implementation

```python
from microsoft_agents.testing import Sample
from aiohttp import web

class MyAgent(Sample):
    async def init_app(self):
        """Initialize your agent"""
        app = web.Application()
        
        # Add routes
        app.router.add_post('/messages', self.handle_messages)
        
        # Setup
        await self.environment.init_env({})
        
        return app
    
    @classmethod
    async def get_config(cls) -> dict:
        return {
            "CLIENT_ID": "your-id",
            "TENANT_ID": "your-tenant",
            "CLIENT_SECRET": "your-secret"
        }
    
    async def handle_messages(self, request):
        """Handle incoming messages"""
        data = await request.json()
        # Process message
        return web.json_response({"ok": True})
```

### Using in Tests

```python
class TestWithSample(Integration):
    _sample_cls = MyAgent
    _agent_url = "http://localhost:3978/"

    @pytest.mark.asyncio
    async def test_with_sample(self, sample: MyAgent):
        # sample is initialized instance
        assert sample is not None
```

## 6. Component Interaction Flow

```
Test Execution Flow:
├─ Integration.setup_method()
│  └─ Load configuration
├─ Create Environment
├─ Initialize Sample (via Environment)
├─ Start Application
├─ Create AgentClient (via fixture)
├─ Create ResponseClient (via fixture)
├─ Run test method
│  ├─ agent_client.send_activity()
│  ├─ response_client.pop()
│  └─ Assert results
├─ Cleanup
│  └─ Close connections
└─ Done
```

## 7. Configuration with SDKConfig

The `SDKConfig` manages environment variables and settings.

### Basic Usage

```python
from microsoft_agents.testing import SDKConfig

# Load from .env file
config = SDKConfig(env_path=".env")

# Access configuration
client_id = config.config["CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"]

# Get connection settings
connection = config.get_connection("SERVICE_CONNECTION")
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `dict` | Read-only copy of configuration |

### Usage in Tests

```python
@pytest.fixture
def sdk_config():
    return SDKConfig(env_path=".env")

@pytest.mark.asyncio
async def test_with_config(self, sdk_config):
    client_id = sdk_config.config["CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"]
    # Use configuration
```

## Complete Example: All Components Together

```python
import pytest
from microsoft_agents.testing import (
    Integration,
    AgentClient,
    ResponseClient,
    AiohttpEnvironment,
    Sample,
    SDKConfig
)
from aiohttp import web

# 1. Define your Sample
class MyAgent(Sample):
    async def init_app(self):
        app = web.Application()
        app.router.add_post('/messages', self.handle_message)
        return app
    
    @classmethod
    async def get_config(cls) -> dict:
        return {"CLIENT_ID": "test"}
    
    async def handle_message(self, request):
        data = await request.json()
        return web.json_response({
            "type": "message",
            "text": f"Echo: {data.get('text')}"
        })

# 2. Create test class
class TestComponents(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    _environment_cls = AiohttpEnvironment
    _sample_cls = MyAgent
    
    @pytest.mark.asyncio
    async def test_all_components(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        # Send via AgentClient
        await agent_client.send_activity("Hello")
        
        # Receive via ResponseClient
        responses = await response_client.pop()
        
        # Verify
        assert len(responses) > 0
        assert "Echo" in responses[0].text
        
        # Cleanup
        await agent_client.close()
```

## Component Selection Guide

| Use Case | Component |
|----------|-----------|
| Writing test classes | `Integration` |
| Sending messages | `AgentClient` |
| Receiving responses | `ResponseClient` |
| Agent-specific logic | `Sample` |
| Environment setup | `Environment` |
| Configuration | `SDKConfig` |

## Summary

The core components work together to provide:

1. **Integration** - Main testing class
2. **AgentClient** - Send activities
3. **ResponseClient** - Receive responses
4. **Environment** - Setup/teardown
5. **Sample** - Your agent code
6. **SDKConfig** - Configuration management

Master these and you can build comprehensive test suites!

---

**Next Steps**:
- [Integration Testing Guide](./INTEGRATION_TESTING.md) - Write complete tests
- [API Reference](./API_REFERENCE.md) - Full API documentation
- [Best Practices](./BEST_PRACTICES.md) - Testing patterns

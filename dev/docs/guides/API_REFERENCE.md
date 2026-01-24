# API Reference

Complete API documentation for the Microsoft Agents Testing Framework.

## Table of Contents

1. [Classes](#classes)
2. [Functions](#functions)
3. [Enums](#enums)
4. [Fixtures](#fixtures)
5. [Decorators](#decorators)

## Classes

### Integration

Base class for integration tests with pytest fixtures.

**Inheritance**: None (base class)

**Location**: `microsoft_agents.testing.integration`

#### Properties

```python
@property
def service_url(self) -> str:
    """Mock response service URL"""
    pass

@property
def agent_url(self) -> str:
    """Agent endpoint URL"""
    pass

@property
def config(self) -> SDKConfig:
    """Loaded SDK configuration"""
    pass
```

#### Methods

```python
def setup_method(self):
    """
    Initialize test configuration.
    Called before each test method.
    
    Loads configuration from _config_path.
    """
    pass

def create_agent_client(self) -> AgentClient:
    """
    Create an AgentClient instance.
    
    Returns:
        AgentClient: Configured client for sending activities
    """
    pass
```

#### Class Attributes

```python
_agent_url: str
    """Agent URL endpoint (required)"""

_service_url: str
    """Response service URL (required)"""

_config_path: str
    """Path to .env configuration file (required)"""

_environment_cls: type[Environment]
    """Environment class to use (optional, default: AiohttpEnvironment)"""

_sample_cls: type[Sample]
    """Sample/agent class to use (optional)"""
```

#### Fixtures

Available as method parameters:

```python
@pytest.fixture
async def environment(self) -> Environment:
    """Test environment instance"""
    pass

@pytest.fixture
async def sample(self) -> Sample:
    """Sample application instance"""
    pass

@pytest.fixture
async def agent_client(self) -> AgentClient:
    """Client for sending activities to agent"""
    pass

@pytest.fixture
async def response_client(self) -> ResponseClient:
    """Client for receiving agent responses"""
    pass
```

#### Example

```python
from microsoft_agents.testing import Integration

class TestMyAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_something(self, agent_client, response_client):
        await agent_client.send_activity("Test")
        responses = await response_client.pop()
        assert len(responses) > 0
```

### AgentClient

Client for sending activities to an agent.

**Location**: `microsoft_agents.testing.integration.client`

#### Constructor

```python
AgentClient(
    agent_url: str,
    cid: str = None,
    client_id: str = None,
    tenant_id: str = None,
    client_secret: str = None,
    service_url: str = None,
    default_activity_data: dict = None,
    default_sleep: float = 0.5
)
```

**Parameters**:
- `agent_url` (str): Agent endpoint URL
- `cid` (str): Conversation ID (auto-generated if None)
- `client_id` (str): Azure AD client ID
- `tenant_id` (str): Azure AD tenant ID
- `client_secret` (str): Azure AD client secret
- `service_url` (str): Response service URL for callbacks
- `default_activity_data` (dict): Default activity field values
- `default_sleep` (float): Default sleep after send (seconds)

#### Methods

```python
async def send_activity(
    activity: Union[Activity, str],
    sleep: float = None
) -> None:
    """
    Send an activity to the agent.
    
    Args:
        activity: Activity object or text string
        sleep: Sleep duration (seconds) after sending
    
    Raises:
        ClientError: If send fails
    """
    pass

async def send_expect_replies(
    activity: Activity,
    sleep: float = None
) -> List[Activity]:
    """
    Send activity and wait for replies.
    
    Args:
        activity: Activity to send
        sleep: Sleep duration after send
    
    Returns:
        List of reply activities
    """
    pass

async def send_invoke_activity(
    activity: Activity,
    sleep: float = None
) -> Any:
    """
    Send invoke activity.
    
    Args:
        activity: Invoke activity
        sleep: Sleep duration
    
    Returns:
        Invoke response
    """
    pass

async def close() -> None:
    """Close client session and cleanup resources."""
    pass
```

#### Example

```python
client = AgentClient(
    agent_url="http://localhost:3978/",
    client_id="app-id",
    tenant_id="tenant-id",
    client_secret="secret",
    service_url="http://localhost:8001/"
)

try:
    # Send text
    await client.send_activity("Hello")
    
    # Send Activity object
    from microsoft_agents.activity import Activity
    activity = Activity(type="message", text="Test")
    await client.send_activity(activity)
    
    # With expect_replies
    replies = await client.send_expect_replies(activity)
finally:
    await client.close()
```

### ResponseClient

Mock service for receiving agent responses.

**Location**: `microsoft_agents.testing.integration.client`

#### Constructor

```python
ResponseClient(
    host: str = "localhost",
    port: int = 9873,
    cid: str = None
)
```

**Parameters**:
- `host` (str): Host address
- `port` (int): Port number
- `cid` (str): Conversation ID

#### Methods

```python
async def pop(self) -> List[Activity]:
    """
    Retrieve and clear received activities.
    
    Returns:
        List of activities received
    """
    pass

async def __aenter__(self) -> 'ResponseClient':
    """Async context manager entry"""
    pass

async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
    """Async context manager exit"""
    pass
```

#### Example

```python
# Manual usage
client = ResponseClient()
responses = await client.pop()

# Context manager
async with ResponseClient() as client:
    responses = await client.pop()
```

### SDKConfig

Configuration loader from environment files.

**Location**: `microsoft_agents.testing.sdk_config`

#### Constructor

```python
SDKConfig(
    env_path: str = ".env",
    load_into_environment: bool = True
)
```

**Parameters**:
- `env_path` (str): Path to .env file
- `load_into_environment` (bool): Load into os.environ

#### Properties

```python
@property
def config(self) -> dict:
    """
    Get configuration dictionary (read-only copy).
    
    Returns:
        Dict with loaded configuration
    """
    pass
```

#### Methods

```python
def get_connection(self, connection_name: str) -> dict:
    """
    Get connection settings by name.
    
    Args:
        connection_name: Connection name (e.g., "SERVICE_CONNECTION")
    
    Returns:
        Connection settings dict
    """
    pass
```

#### Example

```python
config = SDKConfig(env_path=".env")

# Access all config
all_config = config.config

# Get connection
connection = config.get_connection("SERVICE_CONNECTION")
client_id = connection.get("SETTINGS__CLIENTID")
```

### Environment

Base class for test environments.

**Location**: `microsoft_agents.testing.integration.environment`

#### Methods (Abstract)

```python
@abstractmethod
async def init_env(self, environ_config: dict) -> None:
    """
    Initialize environment.
    
    Args:
        environ_config: Configuration dict
    """
    pass

@abstractmethod
def create_runner(self, *args, **kwargs) -> ApplicationRunner:
    """
    Create application runner.
    
    Returns:
        ApplicationRunner instance
    """
    pass
```

### AiohttpEnvironment

Built-in environment for aiohttp-based agents.

**Location**: `microsoft_agents.testing.integration.environment`

Inherits from: `Environment`

#### Usage

```python
from microsoft_agents.testing import AiohttpEnvironment

class TestWithAiohttp(Integration):
    _environment_cls = AiohttpEnvironment
```

### Sample

Base class for agent applications.

**Location**: `microsoft_agents.testing.integration.sample`

#### Constructor

```python
def __init__(self, environment: Environment, **kwargs):
    """
    Initialize sample.
    
    Args:
        environment: Test environment
        **kwargs: Additional arguments
    """
    pass
```

#### Methods (Abstract)

```python
@classmethod
async def get_config(cls) -> dict:
    """
    Get application configuration.
    
    Returns:
        Configuration dict
    """
    pass

@abstractmethod
async def init_app(self):
    """
    Initialize application.
    
    Returns:
        Web application instance
    """
    pass
```

#### Example

```python
from microsoft_agents.testing import Sample
from aiohttp import web

class MyAgent(Sample):
    async def init_app(self):
        app = web.Application()
        app.router.add_post('/messages', self.handle_message)
        return app
    
    @classmethod
    async def get_config(cls) -> dict:
        return {"CLIENT_ID": "test"}
    
    async def handle_message(self, request):
        return web.json_response({"ok": True})
```

## Functions

### generate_token

Generate OAuth token for Azure Bot Service.

**Location**: `microsoft_agents.testing.utils`

```python
def generate_token(
    app_id: str,
    app_secret: str,
    tenant_id: str = None
) -> str:
    """
    Generate OAuth token.
    
    Args:
        app_id: Azure AD app ID
        app_secret: Azure AD app secret
        tenant_id: Azure AD tenant ID
    
    Returns:
        OAuth token string
    
    Raises:
        TokenError: If token generation fails
    """
    pass
```

#### Example

```python
from microsoft_agents.testing import generate_token

token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant"
)
print(f"Token: {token}")
```

### generate_token_from_config

Generate token from SDKConfig.

**Location**: `microsoft_agents.testing.utils`

```python
def generate_token_from_config(config: SDKConfig) -> str:
    """
    Generate token from SDK configuration.
    
    Args:
        config: SDKConfig instance
    
    Returns:
        OAuth token
    """
    pass
```

### populate_activity

Populate activity with default values.

**Location**: `microsoft_agents.testing.utils`

```python
def populate_activity(
    original: Activity,
    defaults: Activity
) -> Activity:
    """
    Populate activity with defaults.
    
    Args:
        original: Original activity
        defaults: Default activity values
    
    Returns:
        Populated activity
    """
    pass
```

### get_host_and_port

Parse host and port from URL.

**Location**: `microsoft_agents.testing.utils`

```python
def get_host_and_port(url: str) -> tuple[str, int]:
    """
    Parse host and port from URL.
    
    Args:
        url: URL string
    
    Returns:
        Tuple of (host, port)
    """
    pass
```

#### Example

```python
from microsoft_agents.testing import get_host_and_port

host, port = get_host_and_port("http://localhost:3978/")
# host = "localhost", port = 3978
```

### ddt

Decorator for data-driven test classes.

**Location**: `microsoft_agents.testing.integration`

```python
def ddt(path: str, prefix: str = "") -> callable:
    """
    Data-driven test decorator.
    
    Args:
        path: Path to YAML test files
        prefix: Prefix for generated test names
    
    Returns:
        Decorator function
    """
    pass
```

## Enums

### FieldAssertionType

Field assertion types for validation.

**Location**: `microsoft_agents.testing.assertions`

```python
class FieldAssertionType(Enum):
    EQUALS = "equals"           # Exact match
    CONTAINS = "contains"       # Contains substring
    EXISTS = "exists"           # Field exists
    NOT_EXISTS = "not_exists"   # Field missing
    GREATER_THAN = "greater_than"  # Greater than
    LESS_THAN = "less_than"     # Less than
```

### AssertionQuantifier

Quantifier for model assertions.

**Location**: `microsoft_agents.testing.assertions`

```python
class AssertionQuantifier(Enum):
    ALL = "all"     # All items must match
    ONE = "one"     # Exactly one match
    NONE = "none"   # No items should match
```

## Fixtures

### environment

**Type**: `pytest.fixture`  
**Scope**: `function`  
**Async**: Yes

Provides test environment instance.

```python
@pytest.fixture
async def environment(self) -> Environment:
    """Test environment"""
    pass
```

### sample

**Type**: `pytest.fixture`  
**Scope**: `function`  
**Async**: Yes

Provides initialized sample application.

```python
@pytest.fixture
async def sample(self, environment) -> Sample:
    """Sample application"""
    pass
```

### agent_client

**Type**: `pytest.fixture`  
**Scope**: `function`  
**Async**: Yes

Provides AgentClient for sending activities.

```python
@pytest.fixture
async def agent_client(self) -> AgentClient:
    """Agent client"""
    pass
```

### response_client

**Type**: `pytest.fixture`  
**Scope**: `function`  
**Async**: Yes

Provides ResponseClient for receiving responses.

```python
@pytest.fixture
async def response_client(self) -> AsyncGenerator[ResponseClient, None]:
    """Response client"""
    pass
```

## Decorators

### pytest.mark.asyncio

Mark test as async for pytest-asyncio.

```python
@pytest.mark.asyncio
async def test_something(self):
    pass
```

### ddt

Data-driven test class decorator.

```python
@ddt("path/to/yaml/")
class TestDataDriven(Integration):
    pass
```

## Type Hints

Common type hints used in API:

```python
from typing import Union, List, Dict, Any, Optional, Tuple
from microsoft_agents.activity import Activity

Union[Activity, str]          # Activity or text
List[Activity]                # List of activities
Dict[str, Any]                # Generic dict
Optional[str]                 # Optional string
Tuple[str, int]               # Tuple of types
```

## Exception Types

### ClientError

Raised when client operations fail.

```python
from microsoft_agents.testing.exceptions import ClientError

try:
    await client.send_activity("Test")
except ClientError as e:
    print(f"Failed: {e}")
```

### TokenError

Raised when token generation fails.

```python
from microsoft_agents.testing.exceptions import TokenError

try:
    token = generate_token(app_id, secret, tenant)
except TokenError as e:
    print(f"Token error: {e}")
```

## Configuration Variables

Environment variables used in configuration:

```
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET
AGENT_URL
SERVICE_URL
LOG_LEVEL
REQUEST_TIMEOUT
RESPONSE_TIMEOUT
```

## Complete API Example

```python
import pytest
from microsoft_agents.testing import (
    Integration,
    AgentClient,
    ResponseClient,
    SDKConfig,
    generate_token,
    get_host_and_port,
    populate_activity,
)
from microsoft_agents.activity import Activity

class CompleteAPIExample(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_api_example(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        # Generate token
        token = generate_token(
            app_id="id",
            app_secret="secret",
            tenant_id="tenant"
        )
        
        # Parse URL
        host, port = get_host_and_port(self.agent_url)
        
        # Create activity
        activity = Activity(type="message", text="Hello")
        defaults = Activity(channelId="directline")
        populated = populate_activity(activity, defaults)
        
        # Send
        await agent_client.send_activity(populated)
        
        # Receive
        responses = await response_client.pop()
        
        assert len(responses) > 0
```

---

**Related**:
- [Best Practices](./BEST_PRACTICES.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Core Components](./CORE_COMPONENTS.md)

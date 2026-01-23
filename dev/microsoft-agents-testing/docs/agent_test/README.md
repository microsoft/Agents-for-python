# Agent Test: End-to-End Agent Testing

A framework for testing M365 Agents SDK agents through end-to-end scenarios. Send activities to your agent and validate responses using a simple, pytest-integrated API.

## Installation

```python
from microsoft_agents.testing.agent_test import (
    agent_test,
    AgentClient,
    AgentScenario,
    ExternalAgentScenario,
    AiohttpAgentScenario,
    AgentEnvironment,
)
```

## Quick Start

```python
import pytest
from microsoft_agents.testing import agent_test, Check

# Test an externally hosted agent
@agent_test("http://localhost:3978")
class TestMyAgent:

    @pytest.mark.asyncio
    async def test_greeting(self, agent_client):
        # Send a message and get responses
        responses = await agent_client.send("Hello!")
        
        # Validate the agent responded with a greeting
        Check(responses).where(type="message").that(text="~Hello")
```

---

## Core Concepts

### The `@agent_test` Decorator

The `@agent_test` decorator transforms a test class by injecting pytest fixtures that provide access to your agent. It handles connection setup, activity routing, and response collection.

```python
# For external agents (already running)
@agent_test("http://localhost:3978")
class TestExternalAgent:
    pass

# For in-process agents (aiohttp-based)
@agent_test(my_agent_scenario)
class TestLocalAgent:
    pass
```

The decorator injects an `agent_client` fixture into your test class, giving you access to send activities and receive responses.

### Agent Scenarios

Scenarios define how your agent is hosted and accessed during tests. The framework provides two main scenarios:

#### `ExternalAgentScenario`

Use this when your agent is already running externally (e.g., in a container or on a remote server).

```python
from microsoft_agents.testing.agent_test import ExternalAgentScenario

# Create a scenario pointing to an external agent
scenario = ExternalAgentScenario("http://my-agent.azurewebsites.net")

@agent_test(scenario)
class TestExternalAgent:
    pass
```

#### `AiohttpAgentScenario`

Use this for testing agents in-process. The framework spins up your agent within the test process, giving you access to internal components for more detailed testing.

```python
from microsoft_agents.testing.agent_test import AiohttpAgentScenario, AgentEnvironment

async def init_my_agent(env: AgentEnvironment):
    """Initialize your agent with the test environment."""
    # Configure your agent using env.agent_application
    app = env.agent_application
    
    @app.on_message
    async def on_message(context):
        await context.send_activity(f"You said: {context.activity.text}")

scenario = AiohttpAgentScenario(init_agent=init_my_agent)

@agent_test(scenario)
class TestLocalAgent:

    @pytest.mark.asyncio
    async def test_echo(self, agent_client):
        responses = await agent_client.send("Hello")
        Check(responses).that(text="~You said: Hello")
```

### The `AgentClient`

The `AgentClient` is your primary interface for interacting with the agent during tests. It provides methods to send activities and collect responses.

```python
@pytest.mark.asyncio
async def test_conversation(self, agent_client):
    # Send a simple text message
    responses = await agent_client.send("What's the weather?")
    
    # Send with a delay to wait for async responses
    responses = await agent_client.send("Tell me more", response_wait=2.0)
    
    # Access all collected activities
    all_activities = agent_client.get_activities()
```

### The `AgentEnvironment`

When using `AiohttpAgentScenario`, additional fixtures become available through the `AgentEnvironment`:

```python
@agent_test(aiohttp_scenario)
class TestWithEnvironment:

    def test_access_components(
        self,
        agent_client,
        agent_environment,
        agent_application,
        storage,
        adapter
    ):
        # Access the full environment
        config = agent_environment.config
        
        # Or individual components directly
        assert agent_application is not None
        assert storage is not None
```

---

## API Reference

### `@agent_test(arg)`

Decorator that transforms a test class for agent testing.

```python
@agent_test(arg: str | AgentScenario) -> Callable[[type], type]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `arg` | `str` | URL of an external agent endpoint |
| `arg` | `AgentScenario` | A scenario instance for custom setup |

**Injected Fixtures:**

| Fixture | Type | Availability |
|---------|------|--------------|
| `agent_client` | `AgentClient` | Always |
| `agent_environment` | `AgentEnvironment` | `AiohttpAgentScenario` only |
| `agent_application` | `AgentApplication` | `AiohttpAgentScenario` only |
| `storage` | `Storage` | `AiohttpAgentScenario` only |
| `adapter` | `ChannelServiceAdapter` | `AiohttpAgentScenario` only |
| `authorization` | `Authorization` | `AiohttpAgentScenario` only |
| `connection_manager` | `Connections` | `AiohttpAgentScenario` only |

---

### `ExternalAgentScenario`

Scenario for testing an externally hosted agent.

#### Constructor

```python
ExternalAgentScenario(
    endpoint: str,
    config: AgentScenarioConfig | None = None
) -> ExternalAgentScenario
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `endpoint` | `str` | Yes | The URL of the external agent |
| `config` | `AgentScenarioConfig` | No | Optional configuration |

---

### `AiohttpAgentScenario`

Scenario for testing an agent hosted in-process with aiohttp.

#### Constructor

```python
AiohttpAgentScenario(
    init_agent: Callable[[AgentEnvironment], Awaitable[None]],
    config: AgentScenarioConfig | None = None,
    use_jwt_middleware: bool = True
) -> AiohttpAgentScenario
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `init_agent` | `Callable` | Yes | Async function to initialize your agent |
| `config` | `AgentScenarioConfig` | No | Optional configuration |
| `use_jwt_middleware` | `bool` | No | Enable JWT auth middleware (default: `True`) |

---

### `AgentClient`

Client for sending activities to an agent and collecting responses.

#### Methods

##### `send()`

```python
async def send(
    self,
    activity_or_text: Activity | str,
    response_wait: float = 0.0
) -> list[Activity | InvokeResponse]
```

Sends an activity to the agent and returns collected responses.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `activity_or_text` | `Activity \| str` | Yes | The activity or text to send |
| `response_wait` | `float` | No | Seconds to wait for async responses (default: `0.0`) |

##### `activity()`

```python
def activity(self, activity_or_str: Activity | str) -> Activity
```

Creates an Activity using the client's activity template.

##### `get_activities()`

```python
def get_activities(self) -> list[Activity]
```

Returns all collected activities from the response collector.

##### `get_invoke_responses()`

```python
def get_invoke_responses(self) -> list[InvokeResponse]
```

Returns all collected invoke responses.

---

### `AgentEnvironment`

Environment containing all components for an in-process agent.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `dict` | SDK configuration dictionary |
| `agent_application` | `AgentApplication` | The agent application instance |
| `authorization` | `Authorization` | Authorization handler |
| `adapter` | `ChannelServiceAdapter` | Channel service adapter |
| `storage` | `Storage` | Storage instance (default: `MemoryStorage`) |
| `connections` | `Connections` | Connection manager |

---

## Integration with Other Modules

### Using with `check`

The `agent_test` module works seamlessly with `Check` for validating responses:

```python
from microsoft_agents.testing import agent_test, Check

@agent_test("http://localhost:3978")
class TestWithCheck:

    @pytest.mark.asyncio
    async def test_validate_responses(self, agent_client):
        responses = await agent_client.send("Hello")
        
        # Filter and assert on responses
        Check(responses).where(type="message").that(text="~greeting")
        
        # Validate typing indicators were sent
        Check(responses).for_any.that(type="typing")
```

### Using with `utils`

Use `ActivityTemplate` to customize how activities are constructed:

```python
from microsoft_agents.testing.utils import ActivityTemplate

# Create a custom activity template
custom_template = ActivityTemplate({
    "channel_id": "custom-channel",
    "locale": "fr-FR",
    "from.name": "Test User",
})

# Apply to agent client
agent_client.activity_template = custom_template
```

---

## Common Patterns and Recipes

### Testing Multi-Turn Conversations

**Use case**: Validate that your agent maintains context across multiple turns.

```python
@pytest.mark.asyncio
async def test_multi_turn(self, agent_client):
    # First turn: set context
    await agent_client.send("My name is Alice")
    
    # Second turn: verify context is retained
    responses = await agent_client.send("What's my name?")
    
    Check(responses).where(type="message").that(text="~Alice")
```

### Testing Typing Indicators

**Use case**: Verify your agent sends typing indicators for better UX.

```python
@pytest.mark.asyncio
async def test_typing_indicator(self, agent_client):
    responses = await agent_client.send("Process this complex request")
    
    # At least one typing indicator should be present
    Check(responses).for_any.that(type="typing")
```

### Testing with Response Delays

**Use case**: Your agent processes asynchronously and sends responses after the initial reply.

```python
@pytest.mark.asyncio
async def test_async_processing(self, agent_client):
    # Wait 3 seconds for async responses
    responses = await agent_client.send(
        "Generate a report",
        response_wait=3.0
    )
    
    Check(responses).where(type="message").that(text="~report complete")
```

### Testing In-Process with State Verification

**Use case**: Verify internal state changes after agent interactions.

```python
@agent_test(my_aiohttp_scenario)
class TestWithStateVerification:

    @pytest.mark.asyncio
    async def test_state_updated(self, agent_client, storage):
        await agent_client.send("Remember: meeting at 3pm")
        
        # Directly verify storage was updated
        # (implementation depends on your storage structure)
        assert storage is not None
```

> See [tests/agent_test/test_agent_test.py](../../tests/agent_test/test_agent_test.py) for more examples.

---

## Limitations

- **Single conversation per test**: Each test method gets a fresh `agent_client`. Conversation state is not preserved across test methods.
- **Local port requirements**: The response server uses port 9378 by default. Ensure this port is available or configure an alternative via `AgentScenarioConfig`.
- **Sync test methods**: The `agent_client` fixture is async and requires `@pytest.mark.asyncio` for test methods.
- **Environment file dependency**: Scenarios look for a `.env` file by default for SDK configuration.

## Potential Improvements

- Support for WebSocket-based agents
- Built-in retry mechanisms for flaky network conditions
- Parallel test execution with isolated agent instances
- Conversation history persistence across test methods
- Support for custom authentication providers

---

## See Also

- [Check Module](../check/README.md) - Validate agent responses
- [Utils Module](../utils/README.md) - Activity templates and data utilities
- [Underscore Module](../underscore/README.md) - Build expressive check conditions

# Microsoft Agents Testing Framework

A testing framework that makes testing M365 Agents simple. Stop writing boilerplate HTTP code and focus on what matters—verifying your agent works correctly.

---

## The Problem

Testing an agent requires a lot of setup. Here's what you'd typically write just to send a message:

```python
# The hard way: ~50 lines of boilerplate for a simple test

import aiohttp
import asyncio
import json
from aiohttp import web

# 1. Get an auth token
async def get_token(app_id: str, app_secret: str, tenant_id: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": app_id,
                "client_secret": app_secret,
                "scope": f"{app_id}/.default",
            }
        ) as resp:
            data = await resp.json()
            return data["access_token"]

# 2. Start a callback server to receive responses
responses = []

async def handle_callback(request):
    data = await request.json()
    responses.append(data)
    return web.Response(text="OK")

app = web.Application()
app.router.add_post("/v3/conversations/{path:.*}", handle_callback)
runner = web.AppRunner(app)

# 3. Build the activity payload
activity = {
    "type": "message",
    "text": "Hello!",
    "channelId": "test",
    "conversation": {"id": "test-conv-123"},
    "from": {"id": "user-1", "name": "Test User"},
    "recipient": {"id": "bot-1", "name": "My Bot"},
    "serviceUrl": "http://localhost:9378/v3/conversations/",
}

# 4. Send the request
async def send_message():
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 9378)
    await site.start()
    
    token = await get_token(APP_ID, APP_SECRET, TENANT_ID)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:3978/api/messages",
            json=activity,
            headers={"Authorization": f"Bearer {token}"}
        ) as resp:
            status = resp.status
    
    await asyncio.sleep(2)  # Wait for callbacks
    await runner.cleanup()
    
    return responses

# 5. Finally, make assertions on the responses
result = asyncio.run(send_message())
assert any("Hello" in str(r) for r in result)
```

**That's a lot of code just to say "Hello" and check the response.**

---

## The Solution

With this framework's pytest integration, the same test becomes:

```python
import pytest
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment
from microsoft_agents.hosting.core import TurnContext, TurnState

async def init_my_agent(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(f"Hello! You said: {context.activity.text}")

scenario = AiohttpScenario(init_agent=init_my_agent, use_jwt_middleware=False)

@pytest.mark.agent_test(scenario)
class TestMyAgent:
    async def test_agent_responds(self, agent_client):
        await agent_client.send("Hi there!", wait=0.2)
        agent_client.expect().that_for_any(text="~Hello")
```

**Pytest fixtures handle everything. No HTTP setup. No callback servers. No context managers.**

---

## Quick Start

### Installation

```bash
pip install microsoft-agents-testing
```

### Your First Test (Pytest Integration)

The fastest way to write agent tests is with the pytest plugin:

```python
import pytest
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment
from microsoft_agents.hosting.core import TurnContext, TurnState


# 1. Define your agent
async def init_echo_agent(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(f"Echo: {context.activity.text}")


# 2. Create a scenario
echo_scenario = AiohttpScenario(
    init_agent=init_echo_agent,
    use_jwt_middleware=False,
)


# 3. Write tests using the marker and fixtures
@pytest.mark.agent_test(echo_scenario)
class TestEchoAgent:
    
    @pytest.mark.asyncio
    async def test_echoes_message(self, agent_client):
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Hello!")

    @pytest.mark.asyncio
    async def test_handles_multiple_messages(self, agent_client):
        await agent_client.send("First")
        await agent_client.send("Second")
        await agent_client.send("Third", wait=0.2)
        
        agent_client.expect().that_for_any(text="Echo: First")
        agent_client.expect().that_for_any(text="Echo: Second")
        agent_client.expect().that_for_any(text="Echo: Third")
```

Run with: `pytest test_echo_agent.py -v`

---

## Pytest Plugin Features

### The `@pytest.mark.agent_test` Marker

Decorate test classes or individual functions to enable agent testing fixtures:

```python
# On a class - all methods get access to fixtures
@pytest.mark.agent_test(my_scenario)
class TestMyAgent:
    async def test_one(self, agent_client):
        ...
    
    async def test_two(self, agent_client):
        ...

# On individual functions
class TestMixedTests:
    @pytest.mark.agent_test(my_scenario)
    async def test_with_agent(self, agent_client):
        ...
    
    def test_regular(self):
        # No agent fixtures needed here
        ...
```

### URL Shorthand for External Agents

Test against a running agent by passing a URL:

```python
@pytest.mark.agent_test("http://localhost:3978/api/messages")
class TestExternalAgent:
    async def test_responds(self, agent_client):
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(type="message")
```

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `agent_client` | Send messages and make assertions on responses |
| `agent_environment` | Access to agent internals (in-process only) |
| `agent_application` | The `AgentApplication` instance |
| `storage` | The `Storage` instance (MemoryStorage) |
| `adapter` | The `ChannelServiceAdapter` |
| `authorization` | The `Authorization` handler |
| `connection_manager` | The `Connections` manager |

### Using Multiple Fixtures

Request any combination of fixtures in your test:

```python
@pytest.mark.agent_test(my_scenario)
class TestWithMultipleFixtures:
    
    @pytest.mark.asyncio
    async def test_full_access(
        self,
        agent_client,
        agent_environment,
        agent_application,
        storage,
        adapter,
    ):
        # Verify environment setup
        assert agent_environment.config is not None
        assert agent_application is agent_environment.agent_application
        
        # Send a message
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="~Hello")
```

### Testing Stateful Agents

Access storage to verify state changes:

```python
async def init_counter_agent(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        count = (state.conversation.get_value("count") or 0) + 1
        state.conversation.set_value("count", count)
        await context.send_activity(f"Message #{count}")


counter_scenario = AiohttpScenario(
    init_agent=init_counter_agent,
    use_jwt_middleware=False,
)


@pytest.mark.agent_test(counter_scenario)
class TestCounterAgent:
    
    @pytest.mark.asyncio
    async def test_counts_messages(self, agent_client, storage):
        await agent_client.send("one")
        await agent_client.send("two")
        await agent_client.send("three", wait=0.2)
        
        agent_client.expect().that_for_any(text="Message #1")
        agent_client.expect().that_for_any(text="Message #2")
        agent_client.expect().that_for_any(text="Message #3")
```

---

## Alternative: Manual Scenario Usage

If you prefer more control or aren't using pytest, use scenarios directly:

```python
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment

async def test_agent_manually():
    scenario = AiohttpScenario(init_agent=init_echo_agent, use_jwt_middleware=False)
    
    async with scenario.client() as client:
        await client.send("Hello!")
        client.expect().that_for_any(text="Echo: Hello!")
```

Or test against an external agent:

```python
from microsoft_agents.testing import ExternalScenario

async def test_external_agent():
    scenario = ExternalScenario("http://localhost:3978/api/messages")
    
    async with scenario.client() as client:
        responses = await client.send("Hello!")
        client.expect().that_for_any(type="message")
```

---

## Core Concepts

### Scenarios

Scenarios manage the test infrastructure lifecycle:

| Scenario | Use Case |
|----------|----------|
| `AiohttpScenario` | In-process testing (fastest, full access to internals) |
| `ExternalScenario` | Test against a running agent at a URL |

### AgentClient

The `agent_client` fixture (or `scenario.client()`) provides:

```python
# Send messages
await agent_client.send("Hello!")
await agent_client.send("Hello!", wait=2.0)  # Wait for async responses

# Make assertions
agent_client.expect().that_for_any(text="~hello")  # Contains "hello"
agent_client.expect().that_for_any(type="message")
agent_client.expect().that_for_none(text="~error")  # No errors

# Access transcript
for exchange in agent_client.ex_history():
    print(f"Sent: {exchange.request.text}")
    for response in exchange.responses:
        print(f"Received: {response.text}")
```

### Fluent Assertions with Expect

```python
# Assert ALL responses match
agent_client.expect().that(type="message")

# Assert ANY response matches
agent_client.expect().that_for_any(text="~hello")

# Assert NO response matches
agent_client.expect().that_for_none(text="~error")

# Assert exactly N responses match
agent_client.expect().that_for_exactly(3, type="message")

# Use lambdas for complex conditions
agent_client.expect().that_for_any(
    text=lambda t: "confirmed" in t.lower() and "order" in t.lower()
)
```

### Filtering with Select

```python
from microsoft_agents.testing import Select

# Get only messages
messages = Select(responses).where(type="message").get()

# Get the last message
last = Select(responses).where(type="message").last().get()

# Chain filters
Select(responses) \
    .where(type="message") \
    .where_not(text="") \
    .first(3) \
    .get()
```

---

## Test Scenarios Comparison

### Pytest Plugin (Recommended)

```python
@pytest.mark.agent_test(scenario)
class TestMyAgent:
    async def test_hello(self, agent_client):
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="~Hello")
```

**Pros:** Minimal boilerplate, automatic fixture management, familiar pytest patterns

### Manual Context Manager

```python
async def test_hello():
    async with scenario.client() as client:
        await client.send("Hello!", wait=0.2)
        client.expect().that_for_any(text="~Hello")
```

**Pros:** Works without pytest, explicit lifecycle control

---

## API Summary

| Component | Purpose |
|-----------|---------|
| `@pytest.mark.agent_test` | Enable agent testing fixtures for a test |
| `agent_client` | Fixture: send activities and make assertions |
| `agent_environment` | Fixture: access agent internals (in-process) |
| `AiohttpScenario` | Test agent in-process (no external server) |
| `ExternalScenario` | Test against a running agent at a URL |
| `Expect` | Fluent assertions on response collections |
| `Select` | Filter and query response collections |
| `Transcript` | Complete conversation history |
| `ActivityTemplate` | Create activities with defaults |

---

## Next Steps

- See [FRAMEWORK.md](FRAMEWORK.md) for the complete feature reference
- Check out the [tests/](../tests/) directory for more examples
- Read module-specific documentation in the source code

---

## License

MIT License - Microsoft Corporation

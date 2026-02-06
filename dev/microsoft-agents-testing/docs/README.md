# Microsoft Agents Testing Framework

A testing framework for M365 Agents that handles auth, callback servers,
activity construction, and response collection so your tests can focus on
what the agent actually does.

```python
async with scenario.client() as client:
    await client.send("Hello!", wait=0.2)
    client.expect().that_for_any(text="Echo: Hello!")
```

## Installation

```bash
pip install -e ./microsoft-agents-testing/
```

## Quick Start

Define your agent, create a scenario, and write tests. The scenario takes
care of hosting, auth tokens, and response plumbing.

### Pytest

```python
import pytest
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment

async def init_echo(env: AgentEnvironment):
    @env.agent_application.activity("message")
    async def on_message(context, state):
        await context.send_activity(f"Echo: {context.activity.text}")

scenario = AiohttpScenario(init_agent=init_echo, use_jwt_middleware=False)

@pytest.mark.agent_test(scenario)
class TestEcho:
    async def test_responds(self, agent_client):
        await agent_client.send("Hi!", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Hi!")
```

```bash
pytest test_echo.py -v
```

### Without pytest

The core has no pytest dependency — use `scenario.client()` as an async
context manager anywhere.

```python
async with scenario.client() as client:
    await client.send("Hi!", wait=0.2)
    client.expect().that_for_any(text="Echo: Hi!")
```

### External agent

To test an agent that's already running (locally or deployed), point
`ExternalScenario` at its endpoint. Auth credentials come from a `.env` file. The path defaults to `.\.venv` but this is configurable at `ExternalScenario` construction.

```python
from microsoft_agents.testing import ExternalScenario

scenario = ExternalScenario("http://localhost:3978/api/messages")
async with scenario.client() as client:
    await client.send("Hello!", wait=1.0)
    client.expect().that_for_any(type="message")
```

## Scenarios

A Scenario manages infrastructure (servers, auth, teardown) and gives you a
client to interact with the agent.

| Scenario | Description |
|----------|-------------|
| `AiohttpScenario` | Hosts the agent in-process — fast, access to internals |
| `ExternalScenario` | Connects to a running agent at a URL |

Swap one for the other and your assertions stay the same.

## AgentClient

The client you get from a scenario. Send messages, collect replies, make
assertions. Pass a string and it becomes a message `Activity` automatically.
Use `wait=` to pause for async callback responses, or use
`send_expect_replies()` when the agent replies inline.

```python
await client.send("Hello!", wait=0.5)              # send + wait for callbacks
replies = await client.send_expect_replies("Hi!")    # inline replies
client.expect().that_for_any(text="~Hello")          # assert
```

Every method has an `ex_` variant (`ex_send`, `ex_invoke`, etc.) that returns
the raw `Exchange` objects instead of just the response activities.

## Expect & Select

Fluent API for asserting on and filtering response collections. `Expect`
raises `AssertionError` with diagnostic context — it shows what was expected,
what was received, and which items were checked. Prefix a value with `~` for
substring matching, or pass a lambda for custom logic. The variable named `x` has a special meaning and is passed in dynamically during evaluation.

```python
client.expect().that_for_any(text="~hello")            # any reply contains "hello"
client.expect().that_for_none(text="~error")           # no reply contains "error"
client.expect().that_for_exactly(2, type="message")    # exactly 2 messages
client.expect().that_for_any(text=lambda x: len(x) > 10)  # lambda predicate
```

`Select` filters and slices before you assert or extract:

```python
from microsoft_agents.testing import Select
selected = Select(client.history()).where(type="message").last(3).get()
Select(client.history()).where(type="message").expect().that(text="~hello")
```

## Transcript

Every request and response is recorded in a `Transcript`. When a test fails
you can print the conversation to see exactly what happened.

`ConversationTranscriptFormatter` gives a chat-style view;
`ActivityTranscriptFormatter` shows all activities with selectable fields.
Both support `DetailLevel` (`MINIMAL`, `STANDARD`, `DETAILED`, `FULL`) and
`TimeFormat` (`CLOCK`, `RELATIVE`, `ELAPSED`).

```python
from microsoft_agents.testing import ConversationTranscriptFormatter, DetailLevel

ConversationTranscriptFormatter(detail=DetailLevel.FULL).print(client.transcript)
```

```
[0.000s] You: Hello!
  (253ms)
[0.253s] Agent: Echo: Hello!
```

## Pytest Plugin

The plugin activates automatically on install. Decorate a class or function
with `@pytest.mark.agent_test(scenario)` — pass a `Scenario` instance, a URL
(creates `ExternalScenario`), or a registered scenario name — and request any
of these fixtures:

| Fixture | Description |
|---------|-------------|
| `agent_client` | Send and assert |
| `agent_environment` | Agent internals (in-process only) |
| `agent_application` | `AgentApplication` instance |
| `storage` | `MemoryStorage` |
| `adapter` | `ChannelServiceAdapter` |
| `authorization` | `Authorization` handler |
| `connection_manager` | `Connections` manager |

## Scenario Registry

Register named scenarios so they can be shared across test files and
referenced by name in pytest markers. Use dot-notation for namespacing
(e.g., `"local.echo"`, `"staging.echo"`) and `discover()` with glob patterns
to find them.

```python
from microsoft_agents.testing import scenario_registry

scenario_registry.register("echo", echo_scenario)
scenario = scenario_registry.get("echo")

# In a test — just pass the name
@pytest.mark.agent_test("echo")
class TestEcho: ...
```

## Documentation

| Document | Contents |
|----------|----------|
| [MOTIVATION.md](MOTIVATION.md) | Before/after code comparison |
| [API.md](API.md) | Public API reference |
| [SAMPLES.md](SAMPLES.md) | Guide to the runnable samples |

## License

MIT License — Microsoft Corporation

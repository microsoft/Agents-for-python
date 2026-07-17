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
`ExternalScenario` at its endpoint.

```python
from microsoft_agents.testing import ExternalScenario

scenario = ExternalScenario("http://localhost:3978/api/messages")
async with scenario.client() as client:
    await client.send("Hello!", wait=1.0)
    client.expect().that_for_any(type="message")
```

## Scenarios

A Scenario manages infrastructure (servers, auth, teardown) and gives you a
client to interact with the agent. Auth credentials and general SDK config settings come from a `.env` file. The path defaults to `.\.env` but this is configurable through `ScenarioConfig` and `ClientConfig`, which are passed in during `Scenario` and `AgentClient` constructions.

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
the raw `Exchange` objects instead of just the response activities. The fluent
shortcuts are typed by collection: `expect()`/`select()` return
`ActivityExpect`/`ActivitySelect`, while `ex_expect()`/`ex_select()` return
`ExchangeExpect`/`ExchangeSelect`.

## Expect & Select

Fluent API for asserting on and filtering response collections. `Expect`
raises `AssertionError` with diagnostic context — it shows what was expected,
what was received, and which items were checked. Prefix a value with `~` for
substring matching, or pass a lambda for custom logic. Lambda parameters named
`x`, `actual`, or `value` receive the resolved value during evaluation.

```python
client.expect().that_for_any(text="~hello")            # any reply contains "hello"
client.expect().that_for_none(text="~error")           # no reply contains "error"
client.expect().that_for_exactly(2, type="message")    # exactly 2 messages
client.expect().that_for_any(text=lambda x: len(x) > 10)  # lambda predicate
```

Use `contains` for nested model, dict, and iterable values. It requires a
callable, dictionary filter, or keyword criteria; `contains()` and
`contains({})` are invalid because an unfiltered predicate would match
everything.

```python
from microsoft_agents.testing.utils import contains

client.expect().that_for_any(
    attachments=contains(content_type="application/vnd.microsoft.card.hero")
)
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

Three formatters are provided:

| Formatter | Output |
|-----------|--------|
| `ConversationTranscriptFormatter` | Human-readable chat lines sorted by timestamp |
| `ActivityTranscriptFormatter` | Flat JSON array of `Activity` objects |
| `JsonTranscriptFormatter` | JSON array of `Exchange` objects (request + responses + metadata) |

```python
from microsoft_agents.testing import (
    ConversationTranscriptFormatter,
    ActivityTranscriptFormatter,
    JsonTranscriptFormatter,
    print_conversation, print_activities, print_json,
)

# Chat-style view
print_conversation(client.transcript)

# Flat JSON activity stream
print_activities(client.transcript)

# Exchange-grouped JSON
print_json(client.transcript)
```

```
[19:42:07.742] You: Hello!
[19:42:07.995] Agent: Echo: Hello!
```

Use `model_dump_args` to control JSON output (e.g. `{"exclude_none": True}`) on the JSON formatters.

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

## CLI

The `agt` CLI lets you test agents interactively from the terminal without writing test code.

```bash
# Show environment info and loaded .env keys
agt env show

# Interactive chat with a running agent
agt scenario chat --url http://localhost:3978/api/messages

# Concurrent load test — 50 requests, 5 s timeout, prints p90 latency
agt scenario load --url http://localhost:3978/api/messages \
    --message "Hello!" --num 50

# List registered scenarios
agt scenario list
```

Use `--agent NAME` instead of `--url` to target a named scenario from `scenario_registry`.

## Documentation

| Document | Contents |
|----------|----------|
| [MOTIVATION.md](MOTIVATION.md) | Before/after code comparison |
| [API.md](API.md) | Public API reference |
| [ASSERTIONS.md](ASSERTIONS.md) | Fluent `Expect`, `Select`, predicates, lambdas, and assertion internals |
| [CLI.md](CLI.md) | `agt` command guide |
| [UTILITIES.md](UTILITIES.md) | `contains`, `poll`, `send`, and `ex_send` helper guide |
| [SAMPLES.md](SAMPLES.md) | Guide to the runnable samples |

## License

MIT License — Microsoft Corporation

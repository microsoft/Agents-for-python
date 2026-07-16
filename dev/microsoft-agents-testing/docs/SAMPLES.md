# Samples

Runnable scripts in `docs/samples/`. Each is self-contained.

| File | What it covers |
|------|----------------|
| `quickstart.py` | Send a message, check the reply |
| `interactive.py` | REPL chat with transcript on exit |
| `scenario_registry_demo.py` | Registering and discovering named scenarios |
| `transcript_formatting.py` | `ConversationTranscriptFormatter`, `ActivityTranscriptFormatter`, `JsonTranscriptFormatter` |
| `deep_dive_assertions.py` | Fluent assertion engine: `Expect`, `Select`, lambdas, typed wrappers, and internals |
| `utilities.py` | `contains`, `poll`, `send`, and `ex_send` helpers |
| `pytest_plugin_usage.py` | `@pytest.mark.agent_test`, fixtures |
| `multi_client.py` | Multiple users, `ActivityTemplate`, child clients |

---

## quickstart.py

Simplest possible test — define an agent, send a message, assert on the reply.

```python
async with scenario.client() as client:
    await client.send("Hello!", wait=0.2)
    client.expect().that_for_any(text="Echo: Hello!")
```

```bash
python -m docs.samples.quickstart
```

---

## interactive.py

REPL loop. Type messages, see replies. Prints the full transcript on exit.

```bash
python -m docs.samples.interactive
```

---

## scenario_registry_demo.py

Register, discover, and look up scenarios by name. Shows dot-notation
namespacing and glob patterns.

```python
scenario_registry.register("local.echo", echo_scenario)
scenario = scenario_registry.get("local.echo")
local = scenario_registry.discover("local.*")
```

```bash
python -m docs.samples.scenario_registry_demo
```

---

## transcript_formatting.py

Demonstrates the three transcript formatters and the convenience print functions.

- `ConversationTranscriptFormatter` — chat-style, timestamped lines
- `ActivityTranscriptFormatter` — flat JSON array of `Activity` objects
- `JsonTranscriptFormatter` — JSON array of `Exchange` objects

```python
from microsoft_agents.testing import (
    ConversationTranscriptFormatter,
    ActivityTranscriptFormatter,
    JsonTranscriptFormatter,
    print_conversation, print_activities, print_json,
)

print_conversation(client.transcript)
print(
    ActivityTranscriptFormatter(
        model_dump_args={"exclude_unset": True, "exclude_none": True}
    ).format(client.transcript)
)
```

```bash
python -m docs.samples.transcript_formatting
```

---

## deep_dive_assertions.py

Walks through the general-purpose fluent assertion engine without requiring a
running agent.

- `Expect` and `Select` over dictionaries
- exact, substring, dictionary, dot-notation, and root callable criteria
- lambda predicates and the `x` / `actual` / `value` convention
- Pydantic model support
- `ActivityExpect`, `ActivitySelect`, `ExchangeExpect`, and `ExchangeSelect`
- `contains`

```python
from microsoft_agents.testing import Expect, Select

items = [{"type": "message", "text": "welcome"}]

Expect(items).that_for_any(type="message", text="~welcome")
Select(items).where(type="message").expect().is_not_empty()
```

```bash
python -m docs.samples.deep_dive_assertions
```

---

## utilities.py

Demonstrates the utility helpers for nested predicates, polling asynchronous
side effects, and one-shot sends to a running agent URL.

- `contains` — searches nested model, dict, and iterable values
- `poll` — waits until a synchronous condition becomes true
- `send` — returns response `Activity` objects from an agent URL
- `ex_send` — returns full `Exchange` objects from an agent URL

```python
from microsoft_agents.testing.utils import contains, poll, send, ex_send

client.expect().that_for_any(
    attachments=contains(content_type="application/vnd.microsoft.card.hero")
)
await poll(lambda: state["saved"], timeout=1.0, interval=0.01)
```

```bash
python -m docs.samples.utilities
```

---

## pytest_plugin_usage.py

Run with `pytest`, not `python`. Shows class and function markers, all
available fixtures, registered scenario names, and `Select`/`Expect`
through the `agent_client` fixture.

```python
@pytest.mark.agent_test(echo_scenario)
class TestEcho:
    async def test_responds(self, agent_client):
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="~Echo")
```

```bash
pytest docs/samples/pytest_plugin_usage.py -v
```

---

## multi_client.py

Multiple clients from one factory, per-client `ActivityTemplate`, child
clients, and transcript scoping.

```python
async with scenario.run() as factory:
    alice = await factory(ClientConfig(activity_template=ActivityTemplate(
        **{"from.id": "alice", "from.name": "Alice"}
    )))
    bob = await factory(ClientConfig(activity_template=ActivityTemplate(
        **{"from.id": "bob", "from.name": "Bob"}
    )))
```

```bash
python -m docs.samples.multi_client
```

---

## CLI

The `agt` CLI is the quickest way to interact with an agent without writing code.

### Interactive chat

```bash
# Chat with an agent running locally
agt scenario chat --url http://localhost:3978/api/messages

# Chat with a registered scenario
agt scenario chat --agent agt.basic
```

Type `/exit` or `/quit` to end the session.

### Load testing

```bash
# Send "Hello!" 50 times concurrently, 5 s timeout
agt scenario load --url http://localhost:3978/api/messages \
    --message "Hello!" --num 50 --timeout 5000

# Send a custom activity from a JSON file
agt scenario load --url http://localhost:3978/api/messages \
    --json_file activity.json --num 20
```

Reports per-request errors and aggregate latency (average, min, max, p90).

### Environment setup

```bash
# Print .env variable names required for auth
agt env help

# Inspect the current environment
agt env show
```

### Listing registered scenarios

```bash
agt scenario list          # all scenarios
agt scenario list "agt.*"  # built-in scenarios
```

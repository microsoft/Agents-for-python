# Samples

Runnable scripts in `docs/samples/`. Each is self-contained.

| File | What it covers |
|------|----------------|
| `quickstart.py` | Send a message, check the reply |
| `interactive.py` | REPL chat with transcript on exit |
| `expect_and_select.py` | `Expect` assertions and `Select` filtering |
| `scenario_registry_demo.py` | Registering and discovering named scenarios |
| `transcript_formatting.py` | Formatters, detail levels, time formats |
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
python docs/samples/quickstart.py
```

---

## interactive.py

REPL loop. Type messages, see replies. Prints the full transcript on exit.

```bash
python docs/samples/interactive.py
```

---

## expect_and_select.py

Walks through `Expect` and `Select` in eight sections: basic assertions,
`~` substring matching, lambdas, quantifiers, collection checks, filtering,
filter-then-assert, and chaining.

```python
client.select() \
    .where(type="message") \
    .last() \
    .expect() \
    .that(text="~Message #3")
```

```bash
python docs/samples/expect_and_select.py
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
python docs/samples/scenario_registry_demo.py
```

---

## transcript_formatting.py

`ConversationTranscriptFormatter`, `ActivityTranscriptFormatter`,
`DetailLevel`, `TimeFormat`, custom labels, and convenience functions.

```python
ConversationTranscriptFormatter(
    detail=DetailLevel.FULL,
    time_format=TimeFormat.ELAPSED,
).print(client.transcript)
```

```bash
python docs/samples/transcript_formatting.py
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
python docs/samples/multi_client.py
```

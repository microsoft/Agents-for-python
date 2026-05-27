# API Reference

```python
from microsoft_agents.testing import (
    AiohttpScenario, ExternalScenario, Scenario, AgentEnvironment,
    AgentClient,
    ScenarioConfig, ClientConfig, ActivityTemplate,
    Expect, Select,
    Transcript, Exchange,
    ConversationTranscriptFormatter, ActivityTranscriptFormatter,
    JsonTranscriptFormatter,
    print_conversation, print_activities, print_json,
    scenario_registry, ScenarioEntry, load_scenarios,
)
```

---

## Scenarios

```
Scenario.run()  →  ClientFactory  →  AgentClient
```

| Scenario | Description |
|----------|-------------|
| `AiohttpScenario` | Hosts the agent in-process via aiohttp `TestServer` |
| `ExternalScenario` | Connects to an agent running at an HTTP URL |

### AiohttpScenario

```python
AiohttpScenario(
    init_agent: Callable[[AgentEnvironment], Awaitable[None]],
    config: ScenarioConfig | None = None,
    use_jwt_middleware: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `init_agent` | `async (AgentEnvironment) -> None` | *(required)* | Callback that registers handlers on the agent |
| `config` | `ScenarioConfig \| None` | `None` | Scenario-level settings (ports, env file, etc.) |
| `use_jwt_middleware` | `bool` | `True` | Enable JWT auth middleware; set `False` for local-only tests |

**Usage:**

```python
async def init_echo(env: AgentEnvironment):
    @env.agent_application.activity("message")
    async def on_message(context, state):
        await context.send_activity(f"Echo: {context.activity.text}")

scenario = AiohttpScenario(init_agent=init_echo, use_jwt_middleware=False)

# Single-client convenience
async with scenario.client() as client:
    await client.send("Hi!", wait=0.2)

# Multi-client via factory
async with scenario.run() as factory:
    alice = await factory(ClientConfig(activity_template=ActivityTemplate(
        **{"from.id": "alice", "from.name": "Alice"}
    )))
    bob = await factory(ClientConfig(activity_template=ActivityTemplate(
        **{"from.id": "bob", "from.name": "Bob"}
    )))
```

### ExternalScenario

```python
ExternalScenario(
    endpoint: str,
    config: ScenarioConfig | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `endpoint` | `str` | *(required)* | Full URL of the agent's `/api/messages` endpoint |
| `config` | `ScenarioConfig \| None` | `None` | Scenario-level settings |

Auth credentials are read from a `.env` file (see `ScenarioConfig.env_file_path`).

```python
scenario = ExternalScenario("http://localhost:3978/api/messages")
async with scenario.client() as client:
    await client.send("Hello!", wait=1.0)
    client.expect().that_for_any(type="message")
```

### AgentEnvironment

Available when using `AiohttpScenario`. Exposes the agent's internals.

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `dict` | SDK configuration dictionary |
| `agent_application` | `AgentApplication` | The running agent application |
| `authorization` | `Authorization` | Auth handler |
| `adapter` | `ChannelServiceAdapter` | Channel adapter |
| `storage` | `Storage` | State storage (typically `MemoryStorage`) |
| `connections` | `Connections` | Connection manager |

### ScenarioConfig

```python
ScenarioConfig(
    env_file_path: str | None = None,
    callback_server_port: int = 9378,
    client_config: ClientConfig = ClientConfig(),
)
```

| Field | Default | Description |
|-------|---------|-------------|
| `env_file_path` | `None` | Path to `.env` file holding environment variables |
| `callback_server_port` | `9378` | Port the callback server binds to |
| `client_config` | `ClientConfig()` | Default client config for all clients |

---

## AgentClient

Created by a scenario. All send methods accept a `str` or an `Activity`.

| Method | Returns | Description |
|--------|---------|-------------|
| `send(text, *, wait=0.0)` | `list[Activity]` | Send a message; `wait` pauses for POST-POST responses |
| `send_expect_replies(text)` | `list[Activity]` | Send with `expect_replies` delivery mode |
| `send_stream(text)` | `list[Activity]` | Send with `stream` delivery mode |
| `invoke(activity)` | `InvokeResponse` | Send an invoke activity; raises on failure |
| `ex_send(text, *, wait=0.0)` | `list[Exchange]` | Like `send` but returns raw `Exchange` objects |
| `ex_send_expect_replies(text)` | `list[Exchange]` | Like `send_expect_replies` but returns Exchanges |
| `ex_send_stream(text)` | `list[Exchange]` | Like `send_stream` but returns Exchanges |
| `ex_invoke(activity)` | `Exchange` | Like `invoke` but returns the Exchange |

`wait` pauses after sending to collect POST-POST responses.

```python
# Simple send
await client.send("Hello!", wait=0.5)

# Expect-replies (inline response, no wait needed)
replies = await client.send_expect_replies("Hello!")

# Custom activity
from microsoft_agents.activity import Activity, ActivityTypes
activity = Activity(type=ActivityTypes.event, name="myEvent", value={"key": "val"})
await client.send(activity, wait=0.5)
```

### Transcript access

| Method | Returns | Description |
|--------|---------|-------------|
| `history()` | `list[Activity]` | All response activities from the root transcript |
| `recent()` | `list[Activity]` | Same as `history()` (full root history) |
| `ex_history()` | `list[Exchange]` | All exchanges from the root transcript |
| `ex_recent()` | `list[Exchange]` | Same as `ex_history()` |
| `clear()` | `None` | Clear the transcript |
| `transcript` | `Transcript` | The underlying `Transcript` object |

### Assertion / selection shortcuts

| Method | Returns | Description |
|--------|---------|-------------|
| `expect(history=False)` | `Expect` | Assert on response activities |
| `select(history=False)` | `Select` | Filter response activities |
| `ex_expect(history=False)` | `Expect` | Assert on exchanges |
| `ex_select(history=False)` | `Select` | Filter exchanges |

```python
# Assert any reply contains "hello" (case-sensitive substring)
client.expect().that_for_any(text="~hello")

# Filter then assert
client.select().where(type="message").expect().that(text="~world")
```

### Child clients

```python
child = client.child()
```

Shares the same sender and template but has its own `Transcript` scope. When a child `Transcript` is cleared, all of its descendents are also cleared but none of its ancestors.

---

## Configuration

### ClientConfig

```python
ClientConfig(
    headers: dict[str, str] = {},
    auth_token: str | None = None,
    activity_template: ActivityTemplate | None = None,
)
```

Builder methods (each returns a new `ClientConfig`):

| Method | Description |
|--------|-------------|
| `with_headers(**headers)` | Add HTTP headers |
| `with_auth_token(token)` | Set a bearer token |
| `with_template(template)` | Set an `ActivityTemplate` for outgoing activities |

### ActivityTemplate

Default field values for outgoing activities. Dot-notation for nested paths.

```python
ActivityTemplate(
    defaults: Activity | dict | None = None,
    **kwargs,
)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `create(original)` | `Activity` | Merge defaults under `original` |
| `with_defaults(...)` | `ActivityTemplate` | Add defaults (does not overwrite existing) |
| `with_updates(...)` | `ActivityTemplate` | Add/overwrite defaults (does not overwrite existing) |

```python
template = ActivityTemplate(**{
    "from.id": "user-42",
    "from.name": "Alice",
    "conversation.id": "conv-abc",
})

# All activities created through this template get those fields as defaults
activity = template.create({"text":"hello", "type": "message"})

# or equivalently
activity = template.create(Activity(text="hello", type="message"))
```

`AgentClient` by default, uses a template with preset dummy values for `channel_id`,
`conversation.id`, `from`, and `recipient`.

---

## Expect

Wraps a collection (Activities, Exchanges, or dicts). Raises `AssertionError`
with diagnostic context on failure.

```python
Expect(items: Iterable[dict | BaseModel])
```

| Method | Passes when… |
|--------|-------------|
| `that(**kwargs)` | **All** items match |
| `that_for_all(**kwargs)` | **All** items match (alias) |
| `that_for_any(**kwargs)` | **At least one** item matches |
| `that_for_none(**kwargs)` | **No** items match |
| `that_for_one(**kwargs)` | **Exactly one** item matches |
| `that_for_exactly(n, **kwargs)` | **Exactly N** items match |

**Collection checks:**

| Method | Passes when… |
|--------|-------------|
| `is_empty()` | Collection has zero items |
| `is_not_empty()` | Collection has at least one item |
| `has_count(n)` | Collection has exactly `n` items |

**Matching rules** — keyword arguments match against item fields:

```python
# Exact match
.that_for_any(type="message")

# Substring match — prefix with ~
.that_for_any(text="~hello")

# Lambda predicate
.that_for_any(text=lambda x: len(x) > 10)

# Multiple fields — all must match on the same item
.that_for_any(type="message", text="~hello")
```

All quantifier methods return `self`, so they can be chained:

```python
client.expect() \
    .that_for_any(text="~hello") \
    .that_for_none(text="~error") \
    .has_count(3)
```

---

## Select

Chainable filtering over a collection.

```python
Select(items: Iterable[dict | BaseModel])
```

| Method | Description |
|--------|-------------|
| `where(**kwargs)` | Keep items matching criteria |
| `where_not(**kwargs)` | Exclude items matching criteria |

Matching rules are the same as `Expect` (exact, `~` substring, lambda).

**Ordering & slicing:**

| Method | Description |
|--------|-------------|
| `order_by(key, reverse=False)` | Sort by field name or callable |
| `first(n=1)` | Keep the first N items |
| `last(n=1)` | Keep the last N items |
| `at(n)` | Keep only the item at index N |
| `sample(n)` | Randomly sample N items |

**Terminal operations:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get()` | `list` | Materialize the selection |
| `count()` | `int` | Number of selected items |
| `empty()` | `bool` | `True` if selection is empty |
| `expect()` | `Expect` | Switch to assertions on the current selection |

```python
from microsoft_agents.testing import Select

messages = Select(client.history()) \
    .where(type="message") \
    .where_not(text="") \
    .last(3) \
    .get()
```

---

## Transcript & Exchange

### Exchange

A single request → response interaction (Pydantic model).

| Field | Type | Description |
|-------|------|-------------|
| `request` | `Activity \| None` | The sent activity |
| `request_at` | `datetime \| None` | When the request was made |
| `status_code` | `int \| None` | HTTP status code |
| `body` | `str \| None` | Raw response body |
| `invoke_response` | `InvokeResponse \| None` | Parsed invoke response |
| `error` | `str \| None` | Error message if failed |
| `responses` | `list[Activity]` | Reply activities |
| `response_at` | `datetime \| None` | When the response arrived |

| Property | Type | Description |
|----------|------|-------------|
| `latency` | `timedelta \| None` | Time between request and response |
| `latency_ms` | `float \| None` | Latency in milliseconds |

### Transcript

Hierarchical collection of exchanges with parent/child scoping.

| Method | Description |
|--------|-------------|
| `record(exchange)` | Add an exchange (propagates to parents) |
| `history()` | Get all exchanges as a list |
| `child()` | Create a child transcript linked to this one |
| `clear()` | Remove all exchanges |
| `get_root()` | Navigate to the root transcript |
| `__len__()` | Number of exchanges |
| `__iter__()` | Iterate over exchanges |

---

## Transcript Formatters

All formatters implement `BaseTranscriptFormatter` and can be used as `formatter.format(transcript)` or called directly as `formatter(transcript)`.

### ConversationTranscriptFormatter

Renders a transcript as a human-readable conversation string. Each activity becomes a timestamped line sorted across the full transcript:

- `[HH:MM:SS.mmm] You: <text>` — user messages
- `[HH:MM:SS.mmm] Agent: <text>` — agent messages
- `[HH:MM:SS.mmm]   --- Agent [<type>] ---` — non-message activity types
- `[HH:MM:SS.mmm] [X] Error: <message>` — errors

```python
ConversationTranscriptFormatter()
```

```
[19:42:07.742] You: Hello!
[19:42:07.995] Agent: Hi there! How can I help?
```

### ActivityTranscriptFormatter

Renders a transcript as a **flat JSON array of `Activity` objects**, interleaving requests and their responses in chronological order. Use this when you need the raw activity stream without exchange grouping.

```python
ActivityTranscriptFormatter(model_dump_args: dict | None = None)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_dump_args` | `None` | Keyword arguments forwarded to `Activity.model_dump_json` (e.g. `{"exclude_unset": True, "exclude_none": True}`) |

```python
formatter = ActivityTranscriptFormatter(model_dump_args={"exclude_none": True})
print(formatter.format(client.transcript))
# → [{"type":"message","text":"Hello!"},{"type":"message","text":"Hi there!"}]
```

### JsonTranscriptFormatter

Renders a transcript as a **JSON array of `Exchange` objects** (request + responses + metadata). Use this to preserve the exchange structure. Use `ActivityTranscriptFormatter` instead for a flat activity list.

```python
JsonTranscriptFormatter(model_dump_args: dict | None = None)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_dump_args` | `None` | Keyword arguments forwarded to `Exchange.model_dump_json` (e.g. `{"exclude_unset": True, "exclude_none": True}`) |

```python
formatter = JsonTranscriptFormatter(model_dump_args={"exclude_none": True})
print(formatter.format(client.transcript))
```

### Convenience Functions

```python
from microsoft_agents.testing import print_conversation, print_activities, print_json

print_conversation(client.transcript)   # ConversationTranscriptFormatter
print_activities(client.transcript)     # ActivityTranscriptFormatter
print_json(client.transcript)           # JsonTranscriptFormatter
```

---

## Scenario Registry

```python
from microsoft_agents.testing import scenario_registry
```

| Method | Description |
|--------|-------------|
| `register(name, scenario, *, description="")` | Register a scenario by name |
| `get(name)` | Retrieve a scenario (raises `KeyError` if missing) |
| `get_entry(name)` | Get the full `ScenarioEntry` (name + scenario + description) |
| `discover(pattern="*")` | Glob-match registered names |
| `__contains__(name)` | Check if a name is registered |
| `__len__()` | Number of registered scenarios |
| `__iter__()` | Iterate over `ScenarioEntry` objects |
| `clear()` | Remove all entries |

**Dot-notation namespacing:**

```python
scenario_registry.register("local.echo", echo_scenario)
scenario_registry.register("local.counter", counter_scenario)

local = scenario_registry.discover("local.*")   # both
echo  = scenario_registry.discover("*.echo")    # just echo
```

**`load_scenarios(module_path)`** imports a Python module by path to trigger
side-effect registrations.

---

## Pytest Plugin

Activated automatically on install.

### Marker

```python
@pytest.mark.agent_test(scenario_or_name)
```

Accepts:
- A `Scenario` instance
- A URL string (creates an `ExternalScenario`)
- A registered scenario name (looks up `scenario_registry`)

Can decorate a class (all methods get fixtures) or individual functions.

### Fixtures

Require the `agent_test` marker.

| Fixture | Type | Scope | Description |
|---------|------|-------|-------------|
| `agent_client` | `AgentClient` | function | Send activities and assert on responses |
| `agent_environment` | `AgentEnvironment` | function | In-process agent internals (AiohttpScenario only) |
| `agent_application` | `AgentApplication` | function | The agent app from the environment |
| `authorization` | `Authorization` | function | Auth handler from the environment |
| `storage` | `Storage` | function | State storage from the environment |
| `adapter` | `ChannelServiceAdapter` | function | Adapter from the environment |
| `connection_manager` | `Connections` | function | Connection manager from the environment |

```python
@pytest.mark.agent_test(my_scenario)
class TestAgent:
    async def test_hello(self, agent_client):
        await agent_client.send("Hi!", wait=0.2)
        agent_client.expect().that_for_any(text="~Hi")

    async def test_state(self, agent_client, storage):
        await agent_client.send("Hello", wait=0.2)
        # inspect storage directly
```

---

## CLI

The `agt` CLI provides interactive commands for testing agents from the terminal without writing test code.

```bash
agt [--env FILE] [--connection NAME] [--verbose]
```

| Global Option | Default | Description |
|---------------|---------|-------------|
| `--env / -e` | `.env` | Path to the `.env` credentials file |
| `--connection / -c` | `SERVICE_CONNECTION` | Named connection for auth credentials |
| `--verbose / -v` | — | Enable verbose output |

---

### `agt env`

Commands for inspecting and setting up the test environment.

#### `agt env show`

Prints Python version, platform, working directory, number of registered scenarios, and the **keys** (not values) of variables loaded from the `.env` file.

```bash
agt env show
agt --env /path/to/other.env env show
```

#### `agt env help`

Prints the required `.env` variable names for authentication so you can scaffold the file.

```bash
agt env help
```

---

### `agt scenario`

Commands for interacting with agents via scenarios. All subcommands accept `--url` or `--agent` to specify the target.

| Option | Description |
|--------|-------------|
| `--url / -u URL` | Connect to an agent at a URL (http or https); creates an `ExternalScenario` |
| `--agent / -a NAME` | Use a named scenario from `scenario_registry` |
| `--module / -m MODULE` | Python module to import first (triggers scenario registrations) |

#### `agt scenario list [PATTERN]`

Lists scenarios registered in `scenario_registry`. Accepts an optional glob `PATTERN` (default `*`).

```bash
agt scenario list          # all registered scenarios
agt scenario list "agt.*"  # built-in scenarios only
```

#### `agt scenario chat`

Starts an interactive REPL session with an agent. Type `/exit` or `/quit` to end the session. Prints a session summary (message count) on exit.

```bash
agt scenario chat --url http://localhost:3978/api/messages
agt scenario chat --agent agt.basic
```

#### `agt scenario load`

Sends the same message or activity to an agent `--num` times concurrently and reports latency statistics. Requests that exceed `--timeout` milliseconds are recorded as timeout errors.

```bash
agt scenario load --url http://localhost:3978/api/messages \
    --message "Hello!" --num 50 --timeout 5000
```

| Option | Default | Description |
|--------|---------|-------------|
| `--message / -m` | — | Text message to send |
| `--json-file / -j` | — | JSON activity file to send |
| `--num / -n` | *(required)* | Number of concurrent requests |
| `--timeout / -t` | `5000` | Milliseconds per request before it is recorded as a timeout error |

Output reports per-request errors followed by aggregate statistics:

```
Request 3 failed with error: Request timed out
Completed 49 requests.
Failed 1 requests.
Average latency: 245.12 ms
Minimum latency: 180.33 ms
Maximum latency: 398.77 ms
90th percentile latency: 320.15 ms
```

---
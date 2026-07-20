# Utilities

The `microsoft_agents.testing.utils` package contains small helpers for common
test tasks that do not need the full fluent API every time:

| Utility | Use it for |
|---------|------------|
| `contains` | Search nested model, dict, and iterable values in `Expect` or `Select` predicates |
| `poll` | Wait for eventually consistent state or asynchronous side effects |
| `send` | Send one activity to a running agent URL and return response activities |
| `ex_send` | Send one activity to a running agent URL and return full `Exchange` objects |

```python
from microsoft_agents.testing.utils import contains, ex_send, poll, send
from microsoft_agents.testing.utils.contains import Contains
```

## `contains`

`contains` is a convenience factory that returns a `Contains` predicate.
`Contains` is a callable object that walks nested Pydantic models,
dictionaries, and iterables until it finds a matching value. Use it when the
value you need is inside a property such as `attachments`, `channel_data`,
entities, or a nested card payload.

```python
client.expect().that_for_any(
    attachments=contains(content_type="application/vnd.microsoft.card.hero")
)
```

### `Contains` class

Use the `contains(...)` function for most tests. Import `Contains` directly when
you want to name, reuse, or configure the predicate before passing it to
`Expect`, `Select`, or plain Python code.

```python
from microsoft_agents.testing.utils.contains import Contains

has_hero_card = Contains(content_type="application/vnd.microsoft.card.hero")

client.expect().that_for_any(attachments=has_hero_card)
hero_replies = client.select().where(has_hero_card).get()
assert has_hero_card(client.history()[0])
```

`Contains` and `contains` accept the same criteria shapes as the fluent
predicate APIs:

```python
contains(lambda value: value == "tenant-1")
contains({"content_type": "application/vnd.microsoft.card.hero"})
contains(content_type="application/vnd.microsoft.card.hero")
contains({"content_type": "thumbnail"}, content_type="hero")
```

The same examples work with the class:

```python
Contains(lambda value: value == "tenant-1")
Contains({"content_type": "application/vnd.microsoft.card.hero"})
Contains(content_type="application/vnd.microsoft.card.hero")
```

Keyword criteria are merged with dictionary criteria, with keyword values taking
precedence for duplicate keys. `contains()` and `contains({})` are invalid
because an unfiltered predicate would match everything. Passing `None` as the
filter is also invalid.

### Matching behavior

`Contains` checks the current value first, then recursively visits nested values:

| Source value | Traversal behavior |
|--------------|--------------------|
| Pydantic model | Visits model field values |
| `dict` | Visits dictionary values |
| Iterable | Visits each item, except strings and bytes |
| Scalar | Stops traversal if the predicate does not match |

For SDK Pydantic models, criteria can use Python field names such as
`content_type`, even when serialized payloads use aliases such as
`contentType`.

### Depth limits

Use `.depth(n)` to limit traversal. The root object is depth `0`; nested model
fields, dictionary values, and iterable items increment the depth by one.
`depth()` returns a new `Contains` instance and does not mutate the original.

```python
deep_search = contains(content_type="hero")
shallow_search = deep_search.depth(1)
```

Depth limits are useful when a broad value predicate could match too deep in a
large payload. For example, `depth(1)` checks the root object and its immediate
children only.

### Common usage patterns

Search within a specific property:

```python
client.expect().that_for_any(
    attachments=contains(content_type="application/vnd.microsoft.card.hero")
)
```

Search anywhere in an activity:

```python
client.expect().that_for_any(
    contains(lambda value: value == "tenant-1")
)
```

Filter before asserting:

```python
hero_messages = client.select().where(
    contains(content_type="application/vnd.microsoft.card.hero")
)
hero_messages.expect().is_not_empty()
```

Reuse a named predicate:

```python
has_error_text = Contains(lambda value: isinstance(value, str) and "error" in value)

client.expect().that_for_none(has_error_text)
```

## `poll`

`poll` repeatedly evaluates a synchronous condition until it returns `True` or
the timeout expires. It is useful when an agent updates memory, writes a file, or
triggers another asynchronous side effect after the response has been sent.

```python
await poll(lambda: state["saved"], timeout=2.0, interval=0.05)
```

`poll` raises `TimeoutError` when the condition never succeeds. The interval
must be non-negative, and the timeout must be greater than or equal to the
interval.

## `send` and `ex_send`

`send` and `ex_send` are convenience helpers for quick checks against an agent
that is already running at an HTTP endpoint.

```python
replies = await send("Hello!", "http://localhost:3978/api/messages")
print(replies[0].text)

exchanges = await ex_send(
    {"type": "message", "text": "Hello from a dict payload"},
    "http://localhost:3978/api/messages",
)
print(exchanges[0].request.text)
```

Both helpers accept a string, a dictionary activity payload, or an `Activity`
instance. Use `send` when you only need response `Activity` objects. Use
`ex_send` when you need the request, response list, invoke response, timing, or
error metadata stored on each `Exchange`.

## Sample

Run the utilities sample for an end-to-end demonstration:

```bash
python -m docs.samples.utilities
```

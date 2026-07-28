# Fluent Assertions

The fluent assertion engine is a general-purpose way to assert over collections
of dictionaries and Pydantic models. It is used by `AgentClient`, but it is not
limited to transcripts or agent tests.

```python
from microsoft_agents.testing import Expect, Select

items = [
    {"type": "message", "text": "welcome"},
    {"type": "typing"},
]

Expect(items).that_for_any(type="message", text="~welcome")
Select(items).where(type="message").expect().that_for_none(text="~error")
```

## Core concepts

| Concept | Use it for |
|---------|------------|
| `Expect` | Assert that items match criteria |
| `Select` | Filter, order, and slice items before asserting or reading them |
| `ActivityExpect` / `ActivitySelect` | Typed wrappers for activity collections |
| `ExchangeExpect` / `ExchangeSelect` | Typed wrappers for exchange collections |

Most tests should start with `Expect(items)` or `Select(items)`.

## `Expect`

`Expect` wraps a collection of dictionaries or Pydantic models and raises an
`AssertionError` when the selected quantifier does not pass.

```python
Expect(items).that_for_any(type="message")
Expect(items).that_for_none(text="~error")
Expect(items).that_for_one(text="hello")
Expect(items).that_for_exactly(2, type="message")
```

| Method | Passes when |
|--------|-------------|
| `that(...)` | All items match |
| `that_for_all(...)` | All items match |
| `that_for_any(...)` | At least one item matches |
| `that_for_none(...)` | No items match |
| `that_for_one(...)` | Exactly one item matches |
| `that_for_exactly(n, ...)` | Exactly `n` items match |

Collection checks are separate from predicate checks:

```python
Expect(items).is_not_empty()
Expect(items).has_count(2)
```

Quantifier methods return `self`, so assertions can be chained:

```python
Expect(items) \
    .that_for_any(text="~hello") \
    .that_for_none(text="~error") \
    .has_count(2)
```

## `Select`

`Select` filters a collection and returns a new selection. Use it when you want
to narrow a collection before asserting or extracting items.

```python
messages = Select(items).where(type="message")

messages.expect().that_for_any(text="~hello")
latest_message = messages.last().get()[0]
```

| Method | Description |
|--------|-------------|
| `where(...)` | Keep matching items |
| `where_not(...)` | Exclude matching items |
| `order_by(key, reverse=False)` | Sort by field name or callable criteria |
| `first(n=1)` | Keep the first `n` items |
| `last(n=1)` | Keep the last `n` items |
| `at(n)` | Keep the item at index `n` |
| `sample(n)` | Randomly sample up to `n` items |
| `get()` | Return the selected items |
| `count()` | Return the selected item count |
| `empty()` | Return whether the selection is empty |
| `expect()` | Switch to assertions over the selection |

`where()` and `where_not()` use the same matching rules as `Expect`.

## Matching rules

Criteria can be provided as keyword arguments, a dictionary, or a root callable.
Multiple criteria on the same assertion must all match the same item.

```python
# Keyword criteria
Expect(items).that_for_any(type="message", text="hello")

# Dictionary criteria
Expect(items).that_for_any({"type": "message", "text": "hello"})

# Root callable criteria
Expect(items).that_for_any(lambda x: x["type"] == "message")
```

### Exact values

Plain values become equality checks.

```python
Expect(items).that_for_any(type="message")
Expect(items).that_for_any(channel_id="msteams")
```

### Substring values

String values starting with `~` become case-sensitive substring checks.

```python
Expect(items).that_for_any(text="~welcome")
Expect(items).that_for_none(text="~error")
```

Use a lambda when you need case-insensitive matching or more complex string
logic.

### Dot-notation paths

Nested values can be matched with dot-notation keys.

```python
activities = [
    {
        "type": "message",
        "conversation": {"id": "conversation-1"},
        "from": {"id": "user-1"},
    }
]

Expect(activities).that_for_any({
    "conversation.id": "conversation-1",
    "from.id": "user-1",
})
```

### Dictionary handling and expansion

Dictionary criteria can be written either as nested dictionaries or as
dot-notation keys. The assertion engine treats both forms the same way:

```python
nested_criteria = {
    "conversation": {"id": "conversation-1"},
    "from": {"id": "user-1"},
}

dot_criteria = {
    "conversation.id": "conversation-1",
    "from.id": "user-1",
}

Expect(activities).that_for_any(nested_criteria)
Expect(activities).that_for_any(dot_criteria)
```

This makes it possible to choose the form that best matches the test: nested
dictionaries are useful when the criteria mirrors a payload shape, while
dot-notation is concise for one-off nested checks.

## Lambdas and callable predicates

Callable predicates let assertions express checks that are awkward as exact or
substring values.

```python
Expect(items).that_for_any(text=lambda x: len(x) > 10)
Select(items).where(attachments=lambda x: len(x) > 0)
```

The current invocation convention is intentionally explicit:

- use a parameter named `x`, `actual`, or `value` to receive the resolved value
- for root callables, that resolved value is the whole item being evaluated
- parameters with other names are not populated by the framework

These examples are equivalent:

```python
Expect(items).that_for_any(text=lambda x: x.startswith("Hello"))
Expect(items).that_for_any(text=lambda actual: actual.startswith("Hello"))
Expect(items).that_for_any(text=lambda value: value.startswith("Hello"))
```

For field criteria, the lambda receives the value at that field:

```python
Expect(items).that_for_any(
    text=lambda x: isinstance(x, str) and len(x) > 20
)
```

For root criteria, the lambda receives the whole dictionary or model:

```python
Expect(items).that_for_any(
    lambda x: x["type"] == "message" and x.get("text")
)
```

Because only `x`, `actual`, and `value` are populated, other parameter names do
not receive the field value:

```python
Expect(items).that_for_any(text=lambda text: text.startswith("Hello"))
```

Prefer naming the parameter `x`, `actual`, or `value` so the predicate is clear
and portable across `Expect`, `Select`, `contains`, and the backend predicate
APIs.

## Pydantic models

The assertion engine accepts Pydantic models as well as dictionaries. Models are
converted to dictionaries for field matching, while root callables receive the
original model object.

```python
from pydantic import BaseModel


class Reply(BaseModel):
    type: str
    text: str


replies = [Reply(type="message", text="welcome")]

Expect(replies).that_for_any(type="message", text="~welcome")
Expect(replies).that_for_any(lambda x: x.text == "welcome")
```

## Typed activity and exchange wrappers

The typed wrappers are specialized versions of `Expect` and `Select` for common
testing package models:

```python
from microsoft_agents.testing import ActivityExpect, ActivitySelect

ActivityExpect(activities).that_for_any(type="message")
ActivitySelect(activities).where(type="message").expect().is_not_empty()
```

`ExchangeExpect` and `ExchangeSelect` work the same way for exchange
collections:

```python
from microsoft_agents.testing import ExchangeExpect, ExchangeSelect

ExchangeExpect(exchanges).that_for_one(status_code=200)
ExchangeSelect(exchanges).where(status_code=200).expect().is_not_empty()
```

## AgentClient shortcuts

`AgentClient` exposes convenience shortcuts for the current transcript. These
shortcuts return the typed wrappers described above:

```python
client.expect()       # ActivityExpect over response activities
client.select()       # ActivitySelect over response activities
client.ex_expect()    # ExchangeExpect over exchanges
client.ex_select()    # ExchangeSelect over exchanges
```

Use these when testing an agent through a scenario:

```python
await client.send("hello", wait=0.5)

client.expect().that_for_any(type="message", text="~hello")
client.ex_expect().that_for_one(status_code=200)
```

## Nested values and `contains`

Use `contains` when the value you care about can be nested inside a model,
dictionary, or iterable, such as attachments, entities, channel data, or card
payloads.

```python
from microsoft_agents.testing.utils import contains

Expect(activities).that_for_any(
    attachments=contains(content_type="application/vnd.microsoft.card.hero")
)
```

`contains` accepts the same criteria shapes as the fluent APIs: callable,
dictionary, or keyword criteria. See [UTILITIES.md](UTILITIES.md) for the full
`Contains` guide.

## Failure descriptions

When an expectation fails, the assertion engine reports:

- how many items matched
- which item indexes matched or failed
- which keys failed on each failed item
- the actual value found at each failed key
- expected values for generated equality predicates when available

This makes exact and substring criteria more diagnosable than opaque custom
predicates, so prefer built-in criteria when they can express the assertion.

## Sample

Run the deep-dive assertions sample for an end-to-end walkthrough of this page:

```bash
python -m docs.samples.deep_dive_assertions
```

# Check: Fluent Response Validation

A fluent API for filtering and asserting on collections of agent responses. Chain selectors and quantifiers to build expressive, readable validations.

## Installation

```python
from microsoft_agents.testing.check import (
    Check,
    Unset,
)
```

## Quick Start

```python
from microsoft_agents.testing.check import Check

# Sample responses from an agent
responses = [
    {"type": "typing"},
    {"type": "message", "text": "Hello! How can I help?"},
    {"type": "message", "text": "I'm your assistant."},
]

# Assert that all messages contain expected text
Check(responses).where(type="message").that(text="~Hello")

# Assert at least one response is a typing indicator
Check(responses).for_any.that(type="typing")

# Get filtered items for further inspection
messages = Check(responses).where(type="message").get()
print(len(messages))  # → 2
```

---

## Core Concepts

### Creating a Check

A `Check` wraps a collection of items (dictionaries or Pydantic models) and provides methods to filter and validate them.

```python
from pydantic import BaseModel

class Message(BaseModel):
    type: str
    text: str | None = None

# From dictionaries
Check([{"type": "message"}, {"type": "typing"}])

# From Pydantic models
Check([Message(type="message", text="Hello")])

# From any iterable
Check(agent_client.get_activities())
```

### Selectors: Filtering Items

Selectors narrow down which items you're working with. They return a new `Check` instance, allowing chaining.

#### `where()` - Include Matching Items

```python
responses = [
    {"type": "message", "text": "hello"},
    {"type": "typing"},
    {"type": "message", "text": "world"},
]

# Filter by field value
messages = Check(responses).where(type="message")
messages.count()  # → 2

# Filter by multiple fields
hello = Check(responses).where(type="message", text="hello")
hello.count()  # → 1

# Chain filters
urgent = Check(responses).where(type="message").where(urgent=True)
```

#### `where_not()` - Exclude Matching Items

```python
# Exclude typing indicators
non_typing = Check(responses).where_not(type="typing")
non_typing.count()  # → 2
```

#### Positional Selectors

```python
# Get the first item
first_msg = Check(responses).first()

# Get the last item
last_msg = Check(responses).last()

# Get item at specific index
second = Check(responses).at(1)

# Limit to first n items
first_two = Check(responses).cap(2)
```

### Quantifiers: How Many Must Match

Quantifiers control how many items must pass the assertion for `that()` to succeed.

```python
responses = [
    {"type": "message", "text": "Hello"},
    {"type": "message", "text": "World"},
    {"type": "typing"},
]

# All items must match (default)
Check(responses).where(type="message").for_all.that(text="~Hello")  # Fails: "World" doesn't match

# At least one must match
Check(responses).for_any.that(type="typing")  # Passes

# None should match
Check(responses).for_none.that(type="error")  # Passes: no errors

# Exactly one must match
Check(responses).for_one.that(text="Hello")  # Passes: exactly one "Hello"
```

| Quantifier | Description |
|------------|-------------|
| `for_all` | Every item must match (default) |
| `for_any` | At least one item must match |
| `for_none` | No items should match |
| `for_one` | Exactly one item must match |
| `for_exactly` | Exactly n items must match |

### Assertions: The `that()` Method

The `that()` method performs the actual assertion. It evaluates the condition against selected items according to the quantifier.

```python
# Assert by field equality
Check(responses).that(type="message")

# Assert by multiple fields
Check(responses).that(type="message", text="Hello")

# Assert with partial match (prefix with ~)
Check(responses).that(text="~Hello")  # text contains "Hello"

# Assert with callable
Check(responses).that(lambda r: len(r.get("text", "")) > 5)

# Assert with dict
Check(responses).that({"type": "message", "urgent": True})
```

### Terminal Operations

Terminal operations end the chain and return values instead of a new `Check`.

```python
responses = [
    {"type": "message", "text": "hello"},
    {"type": "typing"},
]

# Get all selected items as a list
items = Check(responses).where(type="message").get()
# → [{"type": "message", "text": "hello"}]

# Get exactly one item (raises if not exactly one)
item = Check(responses).where(type="typing").get_one()
# → {"type": "typing"}

# Get count of selected items
count = Check(responses).count()
# → 2

# Check if any items exist
has_messages = Check(responses).where(type="message").exists()
# → True
```

---

## API Reference

### `Check`

#### Constructor

```python
Check(
    items: Iterable[dict | BaseModel],
    quantifier: Quantifier = for_all
) -> Check
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | `Iterable[dict \| BaseModel]` | Yes | Collection of items to check |
| `quantifier` | `Quantifier` | No | Default quantifier (default: `for_all`) |

#### Selector Methods

##### `where()`

```python
def where(self, _filter: dict | Callable | None = None, **kwargs) -> Check
```

Filter items that match the criteria. Returns a new `Check` with matching items.

##### `where_not()`

```python
def where_not(self, _filter: dict | Callable | None = None, **kwargs) -> Check
```

Exclude items that match the criteria. Returns a new `Check` without matching items.

##### `first()`

```python
def first(self) -> Check
```

Select only the first item.

##### `last()`

```python
def last(self) -> Check
```

Select only the last item.

##### `at()`

```python
def at(self, n: int) -> Check
```

Select the item at index `n`.

##### `cap()`

```python
def cap(self, n: int) -> Check
```

Limit selection to the first `n` items.

##### `merge()`

```python
def merge(self, other: Check) -> Check
```

Combine items from another `Check` instance.

#### Quantifier Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `for_all` | `Check` | All items must match |
| `for_any` | `Check` | At least one must match |
| `for_none` | `Check` | No items should match |
| `for_one` | `Check` | Exactly one must match |
| `for_exactly` | `Check` | Exactly n must match |

#### Assertion Method

##### `that()`

```python
def that(self, _assert: dict | Callable | None = None, **kwargs) -> bool
```

Assert that selected items match criteria according to the quantifier. Raises `AssertionError` if the assertion fails.

#### Terminal Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get()` | `list[dict \| BaseModel]` | Get all selected items |
| `get_one()` | `dict \| BaseModel` | Get single item (raises if count ≠ 1) |
| `count()` | `int` | Count of selected items |
| `exists()` | `bool` | True if any items selected |

---

### `Unset`

A sentinel value indicating a field was not set. Useful for distinguishing between `None` and "not provided".

```python
from microsoft_agents.testing.check import Unset

# Check if a value was provided
if value is Unset:
    print("Value was not provided")
```

---

## Integration with Other Modules

### Using with `agent_test`

The `Check` class is designed to validate responses from `AgentClient`:

```python
from microsoft_agents.testing import agent_test, Check

@agent_test("http://localhost:3978")
class TestAgent:

    @pytest.mark.asyncio
    async def test_greeting(self, agent_client):
        responses = await agent_client.send("Hello")
        
        # Validate response structure
        Check(responses).where(type="message").that(
            text="~Hello",
            attachments=lambda a: a is None or len(a) == 0
        )
```

### Using with `underscore`

Use placeholder expressions for cleaner, more readable conditions:

```python
from microsoft_agents.testing.check import Check
from microsoft_agents.testing.underscore import _

responses = [
    {"type": "message", "text": "Hello World", "length": 11},
    {"type": "message", "text": "Hi", "length": 2},
]

# Using underscore for conditions
long_messages = Check(responses).where(_.length > 5)
long_messages.count()  # → 1

# In assertions
Check(responses).for_any.that(_.text.startswith("Hello"))
```

---

## Common Patterns and Recipes

### Validating Message Content

**Use case**: Assert that agent responses contain expected text.

```python
# Exact match
Check(responses).where(type="message").that(text="Hello, World!")

# Partial match (contains)
Check(responses).where(type="message").that(text="~Hello")

# Using callable for complex validation
Check(responses).that(
    lambda r: "error" not in r.get("text", "").lower()
)
```

### Checking Response Ordering

**Use case**: Verify that responses arrive in expected order.

```python
# First response should be a typing indicator
Check(responses).first().that(type="typing")

# Last response should be the final message
Check(responses).last().that(text="~Goodbye")

# Specific position
Check(responses).at(1).that(type="message")
```

### Validating Attachments

**Use case**: Assert that responses include expected attachments.

```python
# Has at least one attachment
Check(responses).where(type="message").that(
    attachments=lambda a: a is not None and len(a) > 0
)

# Specific attachment type
Check(responses).that(
    lambda r: any(
        att.get("contentType") == "image/png" 
        for att in r.get("attachments", [])
    )
)
```

### Combining Multiple Checks

**Use case**: Validate different aspects of the response set.

```python
responses = await agent_client.send("Help")

# 1. Should have at least one message
assert Check(responses).where(type="message").exists()

# 2. Should have typing indicator
Check(responses).for_any.that(type="typing")

# 3. No error responses
Check(responses).for_none.that(type="error")

# 4. Exactly 2 message responses
assert Check(responses).where(type="message").count() == 2
```

### Merging Checks

**Use case**: Combine items from multiple sources.

```python
responses1 = await agent_client.send("First message")
responses2 = await agent_client.send("Second message")

# Merge and validate together
all_responses = Check(responses1).merge(Check(responses2))
all_responses.for_all.that(type="message")
```

> See [tests/check/test_check.py](../../tests/check/test_check.py) for more examples.

---

## Limitations

- **Single assertion per `that()` call**: Each `that()` call performs one assertion. Chain multiple calls for multiple validations.
- **No async support**: The `Check` class is synchronous. Collect async responses before checking.
- **Error messages**: Current assertion error messages could be more descriptive for complex conditions.
- **Nested field access**: Deep nested field access requires callables or underscore expressions.

## Potential Improvements

- Enhanced error messages with detailed mismatch information
- Built-in support for JSON path expressions
- Snapshot testing support for response comparison
- Regex pattern matching with `~r/pattern/` syntax
- Async iterator support for streaming responses
- Integration with pytest's assertion introspection

---

## See Also

- [Agent Test Module](../agent_test/README.md) - End-to-end agent testing
- [Underscore Module](../underscore/README.md) - Build expressive conditions with placeholders
- [Utils Module](../utils/README.md) - Data normalization utilities

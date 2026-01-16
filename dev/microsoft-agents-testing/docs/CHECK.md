# microsoft-agents-testing.check

A powerful, fluent assertion library for testing agent responses and structured data. The `Check` class provides unified selection and assertion capabilities for dictionaries and Pydantic models.

## Installation

```python
from microsoft_agents.testing.check import Check
```

## Core Concepts

`Check` provides a chainable API for filtering, selecting, and asserting on collections of items (dictionaries or Pydantic models).

```python
from microsoft_agents.testing.check import Check

responses = [
    {"type": "message", "text": "Hello"},
    {"type": "message", "text": "World"},
    {"type": "typing", "text": None},
]

# Basic usage: filter and assert
Check(responses).where(type="message").that(text="Hello")
```

## Selectors (Filtering)

### `where(**criteria)` - Filter by matching criteria

```python
# Filter by single field
Check(responses).where(type="message")

# Filter by multiple fields
Check(responses).where(type="message", text="Hello")

# Filter using a dict
Check(responses).where({"type": "message"})

# Chainable filtering
Check(responses).where(type="message").where(text="Hello")
```

### `where_not(**criteria)` - Exclude by criteria

```python
# Exclude messages
Check(responses).where_not(type="message")

# Combine with where
Check(responses).where(type="message").where_not(text="Hello")
```

### `first()` - Select only the first item

```python
Check(responses).where(type="message").first()
```

### `last()` - Select only the last item

```python
Check(responses).where(type="message").last()
```

### `at(n)` - Select item at index n

```python
Check(responses).at(2)  # Third item (0-indexed)
```

### `cap(n)` - Limit selection to first n items

```python
Check(responses).cap(3)  # First 3 items only
```

### `merge(other)` - Combine items from another Check

```python
messages = Check(responses).where(type="message")
events = Check(responses).where(type="event")
all_items = messages.merge(events)
```

## Quantifiers

Quantifiers control how assertions are evaluated across the selected items.

### `for_all()` - All items must match (default)

```python
Check(responses).where(type="message").for_all().that(text="Hello")
```

### `for_any()` - At least one item must match

```python
Check(responses).for_any().that(type="typing")
```

### `for_none()` - No items should match

```python
Check(responses).for_none().that(type="error")
```

### `for_one()` - Exactly one item must match

```python
Check(responses).for_one().that(type="typing")
```

### `for_exactly(n)` - Exactly n items must match

```python
Check(responses).for_exactly(2).that(type="message")
```

## Assertions

### `that(**criteria)` - Assert items match criteria

```python
# Simple field assertion
Check(responses).where(type="message").that(text="Hello")

# Multiple field assertion
Check(responses).first().that(type="message", text="Hello")

# Dict-based assertion
Check(responses).first().that({"type": "message", "text": "Hello"})

# Callable assertion on specific fields
Check(responses).where(type="message").that({
    "text": lambda actual: "Hello" in actual
})

# Callable assertion on the entire item
Check(responses).where(type="message").that(
    lambda actual: actual.get("text") is not None
)

# Combined: exact match + callable
Check(responses).first().that({
    "type": "message",
    "text": lambda actual: len(actual) > 3
})
```

### `count_is(n)` - Check item count

```python
Check(responses).where(type="message").count_is(2)  # Returns bool
```

## Terminal Operations

### `get()` - Get selected items as a list

```python
messages = Check(responses).where(type="message").get()
# Returns: [{"type": "message", "text": "Hello"}, ...]
```

### `get_one()` - Get a single item (raises if not exactly one)

```python
msg = Check(responses).where(type="typing").get_one()
# Returns the single item or raises ValueError
```

### `count()` - Get number of selected items

```python
n = Check(responses).where(type="message").count()  # Returns: 2
```

### `exists()` - Check if any items exist

```python
has_messages = Check(responses).where(type="message").exists()  # Returns: True
```

## Working with Pydantic Models

The `Check` class seamlessly works with Pydantic models:

```python
from pydantic import BaseModel

class Message(BaseModel):
    type: str
    text: str | None = None
    attachments: list[dict] | None = None

messages = [
    Message(type="message", text="Hello", attachments=[{"name": "file.txt"}]),
    Message(type="typing"),
]

# Filter and assert
Check(messages).where(type="message").that(text="Hello")

# Assert with callable on a field
Check(messages).where(type="message").that({
    "attachments": lambda actual: len(actual) > 0
})
```

## Complete Example

```python
from microsoft_agents.testing.check import Check

# Sample agent responses
responses = [
    {"type": "typing", "timestamp": 1000},
    {"type": "message", "text": "Hello! How can I help?", "timestamp": 1001},
    {"type": "message", "text": "I found 3 results.", "timestamp": 1002},
    {"type": "message", "text": "Is there anything else?", "timestamp": 1003},
]

# Verify there's exactly one typing indicator
Check(responses).for_one().that(type="typing")

# Verify all messages have text
Check(responses).where(type="message").that({
    "text": lambda actual: actual is not None
})

# Get the first message and verify content
Check(responses).where(type="message").first().that(text="Hello! How can I help?")

# Verify the last message asks a question
Check(responses).where(type="message").last().that({
    "text": lambda actual: "?" in actual
})

# Count messages
msg_count = Check(responses).where(type="message").count()
assert msg_count == 3

# Verify no error responses
Check(responses).for_none().that(type="error")
```

## Quick Reference

| Category | Method | Description |
|----------|--------|-------------|
| **Selectors** | `where(**criteria)` | Filter items matching criteria |
| | `where_not(**criteria)` | Exclude items matching criteria |
| | `first()` | Select first item |
| | `last()` | Select last item |
| | `at(n)` | Select item at index n |
| | `cap(n)` | Limit to first n items |
| | `merge(other)` | Combine with another Check |
| **Quantifiers** | `for_all()` | All must match (default) |
| | `for_any()` | At least one must match |
| | `for_none()` | None should match |
| | `for_one()` | Exactly one must match |
| | `for_exactly(n)` | Exactly n must match |
| **Assertions** | `that(**criteria)` | Assert items match criteria |
| | `count_is(n)` | Check if count equals n |
| **Terminal** | `get()` | Return items as list |
| | `get_one()` | Return single item |
| | `count()` | Return item count |
| | `exists()` | Return True if items exist |
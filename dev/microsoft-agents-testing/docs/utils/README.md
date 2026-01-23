# Utils: Data and Model Utilities

Utilities for working with test data, Pydantic models, and activity templates. Simplify test setup with reusable templates and data normalization.

## Installation

```python
from microsoft_agents.testing.utils import (
    # Model utilities
    normalize_model_data,
    ModelTemplate,
    ActivityTemplate,
    
    # Data utilities
    expand,
    set_defaults,
    deep_update,
)
```

## Quick Start

```python
from microsoft_agents.testing.utils import ActivityTemplate

# Create an activity template with defaults
template = ActivityTemplate({
    "channel_id": "test",
    "from.id": "user-123",
    "from.name": "Test User",
})

# Create activities using the template
activity = template.create({"text": "Hello, agent!"})
print(activity.channel_id)  # → "test"
print(activity.from_.id)    # → "user-123"
print(activity.text)        # → "Hello, agent!"
```

---

## Core Concepts

### Model Templates

Templates let you define reusable defaults for creating Pydantic model instances. This is especially useful for creating test activities with consistent properties.

```python
from microsoft_agents.testing.utils import ModelTemplate
from pydantic import BaseModel

class UserMessage(BaseModel):
    sender: str
    channel: str
    text: str
    priority: int = 0

# Create a template with defaults
template = ModelTemplate(UserMessage, {
    "sender": "test-user",
    "channel": "test-channel",
    "priority": 1,
})

# Create instances - only specify what's different
msg1 = template.create({"text": "Hello"})
msg2 = template.create({"text": "Goodbye", "priority": 5})

print(msg1.sender)    # → "test-user" (from template)
print(msg1.text)      # → "Hello" (from create)
print(msg2.priority)  # → 5 (overridden)
```

### Activity Templates

`ActivityTemplate` is a convenience for creating Activity model templates, pre-configured for the M365 Agents SDK:

```python
from microsoft_agents.testing.utils import ActivityTemplate

# Create with dot notation for nested fields
template = ActivityTemplate({
    "type": "message",
    "channel_id": "teams",
    "conversation.id": "conv-123",
    "from.id": "user-id",
    "from.name": "User Name",
    "recipient.id": "agent-id",
})

# Dot notation is expanded to nested structure
activity = template.create({"text": "Test message"})
print(activity.conversation.id)  # → "conv-123"
print(activity.from_.name)       # → "User Name"
```

### Template Inheritance

Create new templates based on existing ones:

```python
# Base template
base_template = ActivityTemplate({
    "channel_id": "test",
    "locale": "en-US",
})

# Extend with additional defaults (doesn't override existing)
extended = base_template.with_defaults({
    "from.id": "default-user",
    "from.name": "Default User",
})

# Override specific values
french = base_template.with_updates({
    "locale": "fr-FR",
})
```

### Data Normalization

The `normalize_model_data` function converts Pydantic models or dictionaries to a normalized dictionary format, expanding dot notation:

```python
from microsoft_agents.testing.utils import normalize_model_data

# From dictionary with dot notation
data = normalize_model_data({
    "from.id": "user-123",
    "from.name": "User",
    "text": "Hello",
})
# → {"from": {"id": "user-123", "name": "User"}, "text": "Hello"}

# From Pydantic model
from microsoft_agents.activity import Activity
activity = Activity(type="message", text="Hello")
data = normalize_model_data(activity)
# → {"type": "message", "text": "Hello"}
```

### Dictionary Utilities

#### `expand()` - Expand Dot Notation

```python
from microsoft_agents.testing.utils import expand

flat = {
    "user.name": "Alice",
    "user.email": "alice@example.com",
    "active": True,
}

nested = expand(flat)
# → {
#     "user": {
#         "name": "Alice",
#         "email": "alice@example.com"
#     },
#     "active": True
# }
```

#### `deep_update()` - Recursive Dictionary Update

```python
from microsoft_agents.testing.utils import deep_update

original = {
    "user": {"name": "Alice", "role": "admin"},
    "settings": {"theme": "dark"},
}

deep_update(original, {
    "user": {"name": "Bob"},
    "settings": {"language": "en"},
})

# original is now:
# {
#     "user": {"name": "Bob", "role": "admin"},
#     "settings": {"theme": "dark", "language": "en"},
# }
```

#### `set_defaults()` - Set Missing Values

```python
from microsoft_agents.testing.utils import set_defaults

data = {"name": "Alice"}

set_defaults(data, {
    "name": "Default",
    "role": "user",
    "active": True,
})

# data is now: {"name": "Alice", "role": "user", "active": True}
# "name" was not overwritten because it already existed
```

---

## API Reference

### `ModelTemplate[T]`

A generic template for creating Pydantic model instances with predefined defaults.

#### Constructor

```python
ModelTemplate(
    model_class: Type[T],
    defaults: T | dict | None = None,
    **kwargs
) -> ModelTemplate[T]
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_class` | `Type[T]` | Yes | The Pydantic model class |
| `defaults` | `T \| dict \| None` | No | Default values for the template |
| `**kwargs` | `Any` | No | Additional defaults as keyword args |

#### Methods

##### `create()`

```python
def create(self, original: T | dict | None = None) -> T
```

Create a new model instance, applying template defaults to missing fields.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `original` | `T \| dict \| None` | No | Values to merge with defaults |

**Returns**: A new instance of the model class.

##### `with_defaults()`

```python
def with_defaults(
    self,
    defaults: dict | None = None,
    **kwargs
) -> ModelTemplate[T]
```

Create a new template with additional defaults. Existing values in the parent template are not overwritten.

##### `with_updates()`

```python
def with_updates(
    self,
    updates: dict | None = None,
    **kwargs
) -> ModelTemplate[T]
```

Create a new template with updated defaults. Existing values are overwritten by the updates.

---

### `ActivityTemplate`

A `ModelTemplate` specialized for `Activity` models.

```python
ActivityTemplate = functools.partial(ModelTemplate, Activity)
```

Usage is identical to `ModelTemplate`, but you don't need to specify the model class:

```python
# These are equivalent:
template1 = ModelTemplate(Activity, {"type": "message"})
template2 = ActivityTemplate({"type": "message"})
```

---

### `normalize_model_data()`

```python
def normalize_model_data(source: BaseModel | dict) -> dict
```

Convert a Pydantic model or dictionary to a normalized dictionary, expanding dot notation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `BaseModel \| dict` | The model or dict to normalize |

**Returns**: An expanded dictionary.

---

### `expand()`

```python
def expand(data: dict, level_sep: str = ".") -> dict
```

Expand a flattened dictionary with dot-separated keys into a nested dictionary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data` | `dict` | Yes | The flattened dictionary |
| `level_sep` | `str` | No | Separator for nesting levels (default: `.`) |

**Returns**: A nested dictionary.

**Raises**: `RuntimeError` if conflicting keys are found.

---

### `deep_update()`

```python
def deep_update(
    original: dict,
    updates: dict | None = None,
    **kwargs
) -> None
```

Recursively update a dictionary with new values. Modifies `original` in place.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `original` | `dict` | Yes | Dictionary to update |
| `updates` | `dict \| None` | No | Dictionary with update values |
| `**kwargs` | `Any` | No | Additional updates as keyword args |

---

### `set_defaults()`

```python
def set_defaults(
    original: dict,
    defaults: dict | None = None,
    **kwargs
) -> None
```

Set default values in a dictionary. Only adds keys that don't already exist. Modifies `original` in place.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `original` | `dict` | Yes | Dictionary to populate |
| `defaults` | `dict \| None` | No | Dictionary with default values |
| `**kwargs` | `Any` | No | Additional defaults as keyword args |

---

## Integration with Other Modules

### Using with `agent_test`

Activity templates are used by `AgentClient` to construct activities:

```python
from microsoft_agents.testing import agent_test
from microsoft_agents.testing.utils import ActivityTemplate

custom_template = ActivityTemplate({
    "channel_id": "custom-channel",
    "locale": "es-ES",
    "from.id": "spanish-user",
})

@agent_test("http://localhost:3978")
class TestWithCustomTemplate:

    @pytest.mark.asyncio
    async def test_spanish_locale(self, agent_client):
        # Apply custom template
        agent_client.activity_template = custom_template
        
        # Activities will now use Spanish locale by default
        responses = await agent_client.send("Hola")
```

### Using with `check`

Normalize response data before checking:

```python
from microsoft_agents.testing.check import Check
from microsoft_agents.testing.utils import normalize_model_data

# If you have raw response data with dot notation
raw_responses = [
    {"type": "message", "from.name": "Agent"},
]

# Normalize before checking
normalized = [normalize_model_data(r) for r in raw_responses]
Check(normalized).that(type="message")
```

---

## Common Patterns and Recipes

### Creating a Test Activity Suite

**Use case**: Define a set of related activity templates for consistent testing.

```python
from microsoft_agents.testing.utils import ActivityTemplate

# Base template with common properties
BASE_ACTIVITY = ActivityTemplate({
    "channel_id": "test",
    "conversation.id": "test-conv",
    "locale": "en-US",
})

# User message template
USER_MESSAGE = BASE_ACTIVITY.with_defaults({
    "type": "message",
    "from.id": "user-id",
    "from.name": "Test User",
    "recipient.id": "agent-id",
})

# System event template  
SYSTEM_EVENT = BASE_ACTIVITY.with_defaults({
    "type": "event",
    "from.id": "system",
    "name": "system/event",
})

# Use in tests
greeting = USER_MESSAGE.create({"text": "Hello!"})
event = SYSTEM_EVENT.create({"name": "conversation/start"})
```

### Overriding Template Values

**Use case**: Create variations of a template for specific test cases.

```python
# Start with standard template
standard = ActivityTemplate({
    "channel_id": "teams",
    "locale": "en-US",
})

# Create variations
slack_template = standard.with_updates(channel_id="slack")
french_template = standard.with_updates(locale="fr-FR")

# Combine updates
french_slack = standard.with_updates({
    "channel_id": "slack",
    "locale": "fr-FR",
})
```

### Building Nested Structures

**Use case**: Create complex activities with nested properties using dot notation.

```python
from microsoft_agents.testing.utils import ActivityTemplate

template = ActivityTemplate({
    "type": "message",
    "channel_id": "teams",
    # Nested conversation
    "conversation.id": "conv-123",
    "conversation.name": "Test Conversation",
    "conversation.is_group": False,
    # Nested from
    "from.id": "user-id",
    "from.name": "User",
    "from.role": "user",
    # Nested recipient
    "recipient.id": "agent-id",
    "recipient.name": "Agent",
})

activity = template.create({"text": "Complex activity"})
print(activity.conversation.name)  # → "Test Conversation"
```

### Merging Configuration Dictionaries

**Use case**: Combine test configuration from multiple sources.

```python
from microsoft_agents.testing.utils import deep_update, set_defaults

# Base configuration
config = {
    "timeout": 30,
    "retry": {"count": 3, "delay": 1.0},
}

# Environment-specific overrides
env_config = {
    "timeout": 60,
    "retry": {"count": 5},
}

# Apply overrides (modifies config in place)
deep_update(config, env_config)
# config = {"timeout": 60, "retry": {"count": 5, "delay": 1.0}}

# Apply defaults for any missing values
set_defaults(config, {
    "debug": False,
    "retry": {"backoff": 2.0},
})
# Adds "debug": False, doesn't add "backoff" since "retry" exists
```

> See [tests/utils/test_model_utils.py](../../tests/utils/test_model_utils.py) for more examples.

---

## Limitations

- **Dot notation only for dictionaries**: The `expand()` function only works with dictionary inputs. Pydantic models must be normalized first.
- **No circular reference support**: Nested structures must be acyclic.
- **In-place mutations**: `deep_update()` and `set_defaults()` modify the original dictionary. Use `deepcopy` if you need immutability.
- **Single separator character**: The level separator must be a single character (default: `.`).

## Potential Improvements

- Immutable versions of `deep_update()` and `set_defaults()` that return new dictionaries
- Support for array indices in dot notation (e.g., `attachments.0.name`)
- Template validation to catch typos in field names early
- JSON Schema generation from templates for documentation
- Template serialization/deserialization for sharing across test files

---

## See Also

- [Agent Test Module](../agent_test/README.md) - Uses ActivityTemplate for test activities
- [Check Module](../check/README.md) - Validate normalized response data
- [Underscore Module](../underscore/README.md) - Build expressive data transformations

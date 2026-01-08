# Assertions & Validation Guide

Advanced assertion patterns for Microsoft Agents testing.

## Overview

The assertions framework provides sophisticated validation capabilities beyond simple assertions.

## Basic Assertions

### Simple Field Assertions

```python
from microsoft_agents.testing import assert_field, FieldAssertionType

response = agent_response

# Check exists
assert_field(response.text, None, FieldAssertionType.EXISTS)

# Check exact match
assert_field(response.text, "Hello", FieldAssertionType.EQUALS)

# Check contains
assert_field(response.text, "Hello", FieldAssertionType.CONTAINS)
```

## Model Assertions

### Assert Entire Models

```python
from microsoft_agents.testing import assert_model

response = agent_response

# Assert model matches structure
expected = {
    "type": "message",
    "text": "Hello",
}

assert_model(response, expected)
```

## Advanced Query Patterns

### ModelQuery for Complex Validation

```python
from microsoft_agents.testing import ModelQuery

responses = agent_responses

# Query responses
query = ModelQuery(responses)
filtered = query.where(lambda r: "Hello" in r.text)

assert len(filtered) > 0
```

## In Integration Tests

```python
import pytest
from microsoft_agents.testing import Integration, assert_field, FieldAssertionType

class TestWithAssertions(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_response_validation(self, agent_client, response_client):
        await agent_client.send_activity("Hello")
        responses = await response_client.pop()
        
        # Assert on response fields
        assert_field(
            responses[0].text,
            "Hello",
            FieldAssertionType.CONTAINS
        )
```

## Assertion Types

| Type | Usage | Example |
|------|-------|---------|
| EQUALS | Exact match | `text == "Hello"` |
| CONTAINS | Substring match | `"Hello" in text` |
| EXISTS | Field exists | `text is not None` |
| NOT_EXISTS | Field missing | `text is None` |
| GREATER_THAN | Numeric > | `count > 5` |
| LESS_THAN | Numeric < | `count < 10` |

## Combining Assertions

```python
@pytest.mark.asyncio
async def test_combined_assertions(self, agent_client, response_client):
    await agent_client.send_activity("Test")
    responses = await response_client.pop()
    
    # Multiple assertions
    assert len(responses) > 0, "Should have responses"
    assert responses[0].text is not None, "Text should exist"
    assert "Test" in responses[0].text or "OK" in responses[0].text
```

## Custom Assertion Messages

```python
@pytest.mark.asyncio
async def test_with_messages(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    
    assert len(responses) > 0, f"Expected response, got: {responses}"
    assert responses[0].text, f"Response should have text, got: {responses[0]}"
```

---

**Related Guides**:
- [Integration Testing](./INTEGRATION_TESTING.md)
- [Best Practices](./BEST_PRACTICES.md)

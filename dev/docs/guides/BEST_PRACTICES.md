# Best Practices Guide

Proven patterns and recommendations for testing Microsoft Agents effectively.

## Test Organization

### Structure Your Tests

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and config
├── test_basic.py               # Basic functionality
├── test_advanced.py            # Advanced scenarios
├── test_error_handling.py       # Error cases
├── test_performance.py         # Performance-related tests
│
├── fixtures/
│   ├── agents/
│   │   ├── basic_agent.py
│   │   └── complex_agent.py
│   ├── payloads/
│   │   └── sample_activities.json
│   └── scenarios.yaml
│
└── helpers/
    └── test_utils.py           # Helper functions
```

### Use conftest.py for Shared Setup

```python
# tests/conftest.py
import pytest
from microsoft_agents.testing import SDKConfig

@pytest.fixture(scope="session")
def config():
    """Load config once per test session"""
    return SDKConfig(env_path=".env")

@pytest.fixture
def agent_url(config):
    """Get agent URL from config"""
    return config.config.get("AGENT_URL", "http://localhost:3978/")

@pytest.fixture
def service_url(config):
    """Get service URL from config"""
    return config.config.get("SERVICE_URL", "http://localhost:8001/")

@pytest.fixture
def test_data():
    """Provide test data"""
    return {
        "greeting": "Hello",
        "question": "How are you?",
        "complex_query": "What's the capital of France?"
    }
```

## Test Naming Conventions

### Clear, Descriptive Names

```python
# ✓ Good - describes what is tested
def test_agent_responds_to_greeting():
def test_agent_handles_empty_message():
def test_conversation_maintains_context():
def test_agent_returns_error_on_invalid_input():

# ✗ Poor - vague
def test_it_works():
def test_agent1():
def test_complex_scenario_12():
```

### Use Markers for Organization

```python
import pytest

# Mark tests
@pytest.mark.unit
def test_helper_function():
    pass

@pytest.mark.integration
def test_agent_response():
    pass

@pytest.mark.slow
@pytest.mark.asyncio
async def test_long_running_scenario(self, agent_client):
    pass

# Run specific tests
# pytest -m integration
# pytest -m "not slow"
```

## Writing Effective Tests

### Arrange-Act-Assert Pattern

```python
@pytest.mark.asyncio
async def test_agent_greeting(self, agent_client, response_client):
    # Arrange - Setup
    message = "Hello"
    expected_greeting = ["Hello", "Hi", "Greetings"]
    
    # Act - Execute
    await agent_client.send_activity(message)
    responses = await response_client.pop()
    
    # Assert - Verify
    assert len(responses) > 0, "Should receive response"
    assert any(word in responses[0].text for word in expected_greeting)
```

### One Assertion Per Test (When Possible)

```python
# ✓ Good - focused test
@pytest.mark.asyncio
async def test_agent_responds_to_greeting(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    assert len(responses) > 0

# ✓ Good - multiple related assertions are OK
@pytest.mark.asyncio
async def test_response_content(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    assert len(responses) > 0
    assert responses[0].text is not None
    assert len(responses[0].text) > 0

# ✗ Avoid - testing multiple unrelated things
@pytest.mark.asyncio
async def test_everything(self, agent_client, response_client):
    # Greeting
    await agent_client.send_activity("Hi")
    # ... assertions ...
    
    # Question
    await agent_client.send_activity("What's 2+2?")
    # ... assertions ...
    
    # Multiple unrelated things
```

### Use Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("input_text,expected_keyword", [
    ("Hello", "Hello"),
    ("Hi", "Hi"),
    ("Hey", "Hey"),
    ("Greetings", "Greeting"),
])
@pytest.mark.asyncio
async def test_greetings(
    self,
    agent_client,
    response_client,
    input_text: str,
    expected_keyword: str
):
    """Test various greeting styles"""
    await agent_client.send_activity(input_text)
    responses = await response_client.pop()
    assert any(keyword in responses[0].text for keyword in [expected_keyword])
```

## Error Handling & Edge Cases

### Test Error Scenarios

```python
@pytest.mark.asyncio
async def test_empty_message_handling(self, agent_client, response_client):
    """Test agent handles empty input"""
    await agent_client.send_activity("")
    responses = await response_client.pop()
    # Should still respond gracefully
    assert len(responses) > 0

@pytest.mark.asyncio
async def test_long_message_handling(self, agent_client, response_client):
    """Test agent handles very long input"""
    long_text = "X" * 1000
    await agent_client.send_activity(long_text)
    responses = await response_client.pop()
    assert len(responses) > 0

@pytest.mark.asyncio
async def test_special_characters(self, agent_client, response_client):
    """Test handling of special characters"""
    special_text = "!@#$%^&*()_+-=[]{}|;:',.<>?/"
    await agent_client.send_activity(special_text)
    responses = await response_client.pop()
    assert len(responses) > 0
```

### Test Timeout Handling

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_timeout_handling(self, agent_client, response_client):
    """Test behavior when agent is slow"""
    try:
        await agent_client.send_activity("Slow operation")
        
        # Wait with timeout
        responses = await asyncio.wait_for(
            response_client.pop(),
            timeout=5.0
        )
        assert len(responses) > 0
    except asyncio.TimeoutError:
        pytest.fail("Agent response timeout")
```

## Async Testing Best Practices

### Use pytest-asyncio Correctly

```python
import pytest

# ✓ Good - uses decorator
@pytest.mark.asyncio
async def test_async_operation(self, agent_client):
    await agent_client.send_activity("Test")

# ✓ Good - uses fixture
@pytest.fixture
async def async_client():
    client = AgentClient(...)
    yield client
    await client.close()

# ✓ Good - context manager
@pytest.mark.asyncio
async def test_with_context(self, agent_client):
    async with ResponseClient() as rc:
        await agent_client.send_activity("Test")
```

### Handle Async Cleanup

```python
import pytest

@pytest.mark.asyncio
async def test_cleanup(self, agent_client, response_client):
    try:
        await agent_client.send_activity("Test")
        responses = await response_client.pop()
        assert len(responses) > 0
    finally:
        # Always cleanup
        await agent_client.close()
```

## Data Management

### Use Fixtures for Test Data

```python
@pytest.fixture
def conversation_data():
    """Provide test conversation data"""
    return {
        "greeting": "Hello",
        "question": "How are you?",
        "goodbye": "Goodbye"
    }

@pytest.mark.asyncio
async def test_conversation(self, agent_client, conversation_data):
    await agent_client.send_activity(conversation_data["greeting"])
    # ... assertions ...
```

### Store Test Data Externally

```yaml
# tests/fixtures/test_scenarios.yaml
greetings:
  - input: "Hello"
    expected: ["Hello", "Hi"]
  - input: "Hey"
    expected: ["Hey", "Hi"]

questions:
  - input: "How are you?"
    expected_pattern: "I.*[good|well|fine]"
```

Load in tests:

```python
import yaml

@pytest.fixture
def test_scenarios():
    with open("tests/fixtures/test_scenarios.yaml") as f:
        return yaml.safe_load(f)
```

## Integration Testing Patterns

### Multi-Turn Conversation Testing

```python
@pytest.mark.asyncio
async def test_multi_turn_conversation(self, agent_client, response_client):
    """Test multi-step conversation"""
    
    # Step 1: Introduce
    await agent_client.send_activity("Hi, I'm Alice")
    r1 = await response_client.pop()
    assert len(r1) > 0
    
    # Step 2: Ask question
    await agent_client.send_activity("Can you remember my name?")
    r2 = await response_client.pop()
    assert "Alice" in r2[0].text
    
    # Step 3: Goodbye
    await agent_client.send_activity("Bye")
    r3 = await response_client.pop()
    assert len(r3) > 0
```

### Testing Agent With Mock Dependencies

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock_dependency(self, agent_client, response_client):
    """Test agent with mocked external service"""
    
    with patch('agent.services.external_api') as mock_api:
        # Setup mock
        mock_api.get_data = AsyncMock(return_value={"result": "mocked"})
        
        # Test
        await agent_client.send_activity("Get data")
        responses = await response_client.pop()
        
        # Verify mock was called
        mock_api.get_data.assert_called_once()
        assert len(responses) > 0
```

## Performance Testing

### Basic Performance Test

```python
import time

@pytest.mark.performance
@pytest.mark.asyncio
async def test_response_time(self, agent_client, response_client):
    """Test agent responds within acceptable time"""
    
    start = time.time()
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    duration = time.time() - start
    
    assert duration < 1.0, f"Response took {duration}s, expected < 1s"
```

### Load Testing Integration

```python
@pytest.mark.slow
def test_concurrent_load(self):
    """Test agent under load"""
    import concurrent.futures
    
    def send_message():
        # Send activity
        pass
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_message) for _ in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert all(r for r in results)
```

## Debugging Tips

### Use Logging

```python
import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_with_logging(self, agent_client, response_client):
    logger.info("Starting test")
    
    logger.debug("Sending activity...")
    await agent_client.send_activity("Test")
    
    logger.debug("Getting responses...")
    responses = await response_client.pop()
    
    logger.info(f"Received {len(responses)} responses")
    assert len(responses) > 0
```

Configure logging:

```python
# tests/conftest.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Use Print Debugging

```python
@pytest.mark.asyncio
async def test_with_debug_print(self, agent_client, response_client):
    await agent_client.send_activity("Test")
    responses = await response_client.pop()
    
    # Print detailed info
    print("\n=== Debug Info ===")
    print(f"Response count: {len(responses)}")
    if responses:
        print(f"Response text: {responses[0].text}")
        print(f"Response type: {responses[0].type}")
        if hasattr(responses[0], 'from'):
            print(f"From: {responses[0].from}")
```

Run with output:

```bash
pytest tests/test_file.py::test_with_debug_print -v -s
```

## Continuous Integration

### pytest.ini for CI

```ini
[pytest]
# CI-friendly settings
asyncio_mode = auto
addopts = 
    -v
    --tb=short
    --maxfail=3
    --timeout=300

# Mark slow tests
markers =
    slow: slow tests to skip in CI
    integration: integration tests

testpaths = tests
```

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short
```

## Summary of Best Practices

✅ **DO**:
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Use fixtures for shared setup
- Test error cases and edge cases
- Use parametrized tests for similar scenarios
- Keep tests focused and independent
- Use markers to organize tests
- Handle async cleanup properly
- Log important information
- Document complex test scenarios

❌ **DON'T**:
- Write tests with unclear names
- Test multiple unrelated things in one test
- Skip error handling tests
- Ignore timeouts
- Leave resources open
- Write flaky tests that sometimes fail
- Copy-paste test code
- Ignore logging/debugging info
- Test implementation details instead of behavior
- Skip cleanup and teardown

---

**Related Guides**:
- [Integration Testing](./INTEGRATION_TESTING.md)
- [Performance Testing](./PERFORMANCE_TESTING.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

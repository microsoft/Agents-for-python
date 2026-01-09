+# Integration Testing Guide

Learn how to write comprehensive integration tests for your Microsoft Agents.

## What is Integration Testing?

Integration testing verifies that your agent works correctly by:
- Sending real activities
- Receiving actual responses
- Testing end-to-end flows
- Validating agent behavior

Unlike unit tests that test individual functions, integration tests test the entire agent in a realistic environment.

## Basic Integration Test

### Minimal Example

```python
import pytest
from microsoft_agents.testing import Integration, AgentClient, ResponseClient

class TestBasicAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_agent_responds(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        # Send message
        await agent_client.send_activity("Hello")
        
        # Get response
        responses = await response_client.pop()
        
        # Assert
        assert len(responses) > 0
```

## Project Structure

Organize your tests effectively:

```
project/
├── agent/                      # Your agent code
│   ├── main.py
│   ├── handlers/
│   └── models/
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures
│   ├── test_integration.py    # Your integration tests
│   ├── fixtures/              # Test data
│   └── scenarios.yaml         # DDT tests
└── .env                        # Configuration
```

## Setting Up Tests

### Step 1: Create Test Class

```python
import pytest
from microsoft_agents.testing import (
    Integration,
    AgentClient,
    ResponseClient,
    AiohttpEnvironment
)

class TestMyAgent(Integration):
    """Test suite for my agent"""
    
    # Required configuration
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    # Optional: specify environment and sample
    # _environment_cls = AiohttpEnvironment
    # _sample_cls = MyAgentSample
```

### Step 2: Configure pytest

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
markers =
    asyncio: marks tests as async
    integration: marks tests as integration
```

### Step 3: Create conftest.py

```python
# tests/conftest.py
import pytest
from microsoft_agents.testing import SDKConfig

@pytest.fixture
def config():
    """Load SDK configuration"""
    return SDKConfig(env_path=".env")

@pytest.fixture
def agent_url(config):
    """Get agent URL from config"""
    return config.config.get("AGENT_URL", "http://localhost:3978/")
```

## Writing Test Methods

### Pattern 1: Simple Message Test

```python
@pytest.mark.asyncio
async def test_greeting(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent greets user"""
    
    # Arrange - prepare message
    message = "Hello"
    
    # Act - send message
    await agent_client.send_activity(message)
    
    # Assert - check response
    responses = await response_client.pop()
    assert len(responses) > 0
    assert responses[0].text is not None
```

### Pattern 2: Content Validation

```python
@pytest.mark.asyncio
async def test_specific_response(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent returns specific content"""
    
    await agent_client.send_activity("What's your name?")
    responses = await response_client.pop()
    
    # Check content
    assert len(responses) > 0
    response_text = responses[0].text
    assert "I am" in response_text or "My name is" in response_text
```

### Pattern 3: Conversation Flow

```python
@pytest.mark.asyncio
async def test_conversation_flow(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test multi-turn conversation"""
    
    # Turn 1: Greeting
    await agent_client.send_activity("Hi")
    responses = await response_client.pop()
    assert len(responses) > 0
    greeting = responses[0]
    
    # Turn 2: Question
    await agent_client.send_activity("How can you help?")
    responses = await response_client.pop()
    assert len(responses) > 0
    help_response = responses[0]
    
    # Turn 3: Goodbye
    await agent_client.send_activity("Goodbye")
    responses = await response_client.pop()
    assert len(responses) > 0
```

### Pattern 4: Multiple Responses

```python
@pytest.mark.asyncio
async def test_multiple_responses(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent sending multiple responses"""
    
    await agent_client.send_activity("Tell me a story")
    responses = await response_client.pop()
    
    # Check for multiple parts
    assert len(responses) >= 2  # Expect 2+ responses
    
    for i, response in enumerate(responses):
        print(f"Response {i+1}: {response.text}")
```

### Pattern 5: Rich Content

```python
@pytest.mark.asyncio
async def test_rich_content(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent returns rich content"""
    
    await agent_client.send_activity("Show me a card")
    responses = await response_client.pop()
    
    assert len(responses) > 0
    response = responses[0]
    
    # Check for attachments (cards, images, etc.)
    if hasattr(response, 'attachments'):
        assert len(response.attachments) > 0
        print(f"Attachment type: {response.attachments[0].content_type}")
```

### Pattern 6: Error Handling

```python
@pytest.mark.asyncio
async def test_error_handling(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent handles errors gracefully"""
    
    # Send invalid request
    await agent_client.send_activity("")  # Empty message
    responses = await response_client.pop()
    
    # Agent should still respond
    assert len(responses) > 0
    # Could return error message or ask for clarification
```

### Pattern 7: Using expect_replies

```python
@pytest.mark.asyncio
async def test_with_expect_replies(self, agent_client: AgentClient):
    """Test using send_expect_replies"""
    from microsoft_agents.activity import Activity
    
    # Create activity
    activity = Activity(
        type="message",
        text="Hello?",
        channelId="directline"
    )
    
    # Send and wait for replies
    replies = await agent_client.send_expect_replies(activity)
    
    assert len(replies) > 0
    assert replies[0].text is not None
```

### Pattern 8: Custom Activity

```python
@pytest.mark.asyncio
async def test_custom_activity(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test with custom activity properties"""
    from microsoft_agents.activity import Activity
    
    activity = Activity(
        type="message",
        text="Test",
        from_="user@example.com",
        locale="en-US",
        channelId="directline"
    )
    
    await agent_client.send_activity(activity)
    responses = await response_client.pop()
    
    assert len(responses) > 0
```

## Testing Different Scenarios

### Testing Keywords/Intent

```python
@pytest.mark.parametrize("keyword,expected", [
    ("help", "How can I"),
    ("hello", "Hello"),
    ("thanks", "You're welcome"),
])
@pytest.mark.asyncio
async def test_keywords(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient,
    keyword: str,
    expected: str
):
    """Test agent responds to keywords"""
    
    await agent_client.send_activity(keyword)
    responses = await response_client.pop()
    
    assert len(responses) > 0
    assert expected in responses[0].text
```

### Testing State Management

```python
@pytest.mark.asyncio
async def test_conversation_context(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent maintains conversation context"""
    
    # First message
    await agent_client.send_activity("My name is Alice")
    responses1 = await response_client.pop()
    assert len(responses1) > 0
    
    # Second message referencing name
    await agent_client.send_activity("Remember my name?")
    responses2 = await response_client.pop()
    assert len(responses2) > 0
    
    # Should reference "Alice"
    assert "Alice" in responses2[0].text
```

### Testing Timeout Handling

```python
import asyncio

@pytest.mark.asyncio
async def test_timeout_handling(
    self,
    agent_client: AgentClient,
    response_client: ResponseClient
):
    """Test agent handles slow operations"""
    
    # Send message that might take time
    await agent_client.send_activity("Run long operation")
    
    # Wait for response with timeout
    try:
        responses = await asyncio.wait_for(
            response_client.pop(),
            timeout=10.0  # 10 second timeout
        )
        assert len(responses) > 0
    except asyncio.TimeoutError:
        pytest.fail("Agent took too long to respond")
```

## Fixtures and Setup/Teardown

### Class-Level Setup

```python
class TestAgentSetup(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    def setup_method(self):
        """Run before each test"""
        super().setup_method()
        # Add custom setup here
        self.test_data = {"greeting": "Hello"}
    
    def teardown_method(self):
        """Run after each test"""
        # Cleanup here
        self.test_data = None
```

### Using Fixtures

```python
@pytest.fixture
async def agent_with_greeting(agent_client):
    """Fixture that sends greeting first"""
    await agent_client.send_activity("Hello")
    # ResponseClient would receive this
    return agent_client

@pytest.mark.asyncio
async def test_with_greeting(self, agent_with_greeting, response_client):
    """Test using custom fixture"""
    # Agent already greeted
    await agent_with_greeting.send_activity("How are you?")
    responses = await response_client.pop()
    assert len(responses) > 0
```

## Assertions Best Practices

### Good Assertions

```python
# ✓ Specific
assert len(responses) > 0
assert responses[0].text is not None
assert "Hello" in responses[0].text

# ✓ Clear error messages
assert len(responses) > 0, "Expected at least one response"
assert "Hello" in responses[0].text, f"Expected 'Hello' in response, got: {responses[0].text}"
```

### Avoid

```python
# ✗ Too broad
assert responses

# ✗ No context
assert responses[0]

# ✗ Unclear
assert len(responses) == 1
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test

```bash
pytest tests/test_integration.py::TestMyAgent::test_greeting -v
```

### Run with Output

```bash
pytest tests/ -v -s
```

### Run with Markers

```bash
# Run only integration tests
pytest tests/ -m integration

# Run all except slow tests
pytest tests/ -m "not slow"
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

## Debugging Tests

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_debug(self, agent_client, response_client):
    logging.debug("Sending message...")
    await agent_client.send_activity("Hello")
    logging.debug("Waiting for response...")
    responses = await response_client.pop()
    logging.debug(f"Received {len(responses)} responses")
```

### Use pdb Debugger

```python
@pytest.mark.asyncio
async def test_with_debug(self, agent_client, response_client):
    await agent_client.send_activity("Test")
    responses = await response_client.pop()
    
    # Drop into debugger
    import pdb; pdb.set_trace()
    
    assert len(responses) > 0
```

### Print Debug Info

```python
@pytest.mark.asyncio
async def test_with_print_debug(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    
    print(f"\n=== Debug Info ===")
    print(f"Responses: {len(responses)}")
    for i, resp in enumerate(responses):
        print(f"  {i}: {resp.text}")
        print(f"     Type: {resp.type}")
        if hasattr(resp, 'attachments'):
            print(f"     Attachments: {len(resp.attachments)}")
```

## Complete Example

```python
import pytest
from microsoft_agents.testing import Integration, AgentClient, ResponseClient
import asyncio

class TestCompleteExample(Integration):
    """Complete integration test example"""
    
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    def setup_method(self):
        """Setup before each test"""
        super().setup_method()
        self.test_messages = []
    
    @pytest.mark.asyncio
    async def test_greeting_flow(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test complete greeting flow"""
        
        # Greet
        await agent_client.send_activity("Hello")
        responses = await response_client.pop()
        assert len(responses) > 0, "Should have greeting response"
        self.test_messages.append(responses[0].text)
        
        # Ask question
        await agent_client.send_activity("How are you?")
        responses = await response_client.pop()
        assert len(responses) > 0, "Should have response to question"
        self.test_messages.append(responses[0].text)
        
        # Verify conversation happened
        assert len(self.test_messages) == 2
        print("Conversation flow:")
        for msg in self.test_messages:
            print(f"  - {msg}")
    
    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent handles errors"""
        
        # Send empty message
        await agent_client.send_activity("")
        responses = await response_client.pop()
        
        # Agent should respond (error message or clarification request)
        assert len(responses) > 0, "Should respond to empty message"
        
        # Send valid message after error
        await agent_client.send_activity("Hello")
        responses = await response_client.pop()
        assert len(responses) > 0, "Should recover after error"
```

## Summary

Key points for integration testing:

1. **Extend Integration** - Base your tests on the Integration class
2. **Use Fixtures** - Leverage agent_client and response_client fixtures
3. **Test Flows** - Test complete conversation flows
4. **Assert Responses** - Validate agent responses
5. **Handle Async** - Use @pytest.mark.asyncio for async tests
6. **Debug** - Use print, logging, or pdb for debugging
7. **Organize** - Keep tests organized in clear structure

---

**Next Steps**:
- [Data-Driven Testing](./DATA_DRIVEN_TESTING.md) - YAML-based tests
- [Assertions Guide](./ASSERTIONS.md) - Advanced assertions
- [Performance Testing](./PERFORMANCE_TESTING.md) - Load testing

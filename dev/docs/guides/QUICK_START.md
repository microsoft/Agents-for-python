# Quick Start Guide

Get the Microsoft Agents Testing Framework up and running in 5 minutes!

## Prerequisites

- Python 3.10 or later
- pip package manager
- An agent project (or ready to create one)
- Azure Bot Service credentials (for some tests)

## Step 1: Installation (1 minute)

```bash
# Install the framework
pip install microsoft-agents-testing

# Verify installation
python -c "import microsoft_agents.testing; print('Success!')"
```

## Step 2: Setup Environment (1 minute)

Create a `.env` file in your project root:

```env
# Azure Bot Service Credentials
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-client-secret

# Your Agent Details
AGENT_URL=http://localhost:3978/
SERVICE_URL=http://localhost:8001/
```

## Step 3: Create Your First Test (2 minutes)

Create `tests/test_agent.py`:

```python
import pytest
from microsoft_agents.testing import Integration, AgentClient, ResponseClient

class TestMyAgent(Integration):
    """Test suite for my agent"""
    
    # Configure your agent
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"

    @pytest.mark.asyncio
    async def test_agent_responds(
        self, 
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test that agent responds to a greeting"""
        
        # Send a message to the agent
        await agent_client.send_activity("Hello agent!")
        
        # Wait for and retrieve responses
        responses = await response_client.pop()
        
        # Verify we got a response
        assert len(responses) > 0
        print(f"Agent responded: {responses[0].text}")

    @pytest.mark.asyncio
    async def test_agent_question(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent handles questions"""
        
        # Send a question
        await agent_client.send_activity("What time is it?")
        
        # Get response
        responses = await response_client.pop()
        
        # Validate response exists
        assert len(responses) > 0
        assert responses[0].text is not None
```

## Step 4: Run Your Test (1 minute)

```bash
# Run all tests
pytest tests/test_agent.py -v

# Run a specific test
pytest tests/test_agent.py::TestMyAgent::test_agent_responds -v

# Run with output
pytest tests/test_agent.py -v -s
```

## Step 5 (Optional): Try Data-Driven Testing

Create `tests/agent_scenarios.yaml`:

```yaml
name: "Agent Greeting Scenarios"
scenarios:
  - name: "Greeting Test"
    send:
      type: "message"
      text: "Hello!"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Question Test"
    send:
      type: "message"
      text: "What is 2 + 2?"
    assert:
      - type: "exists"
        path: "text"
```

Run it:

```bash
aclip --env_path .env ddt ./tests/agent_scenarios.yaml -v
```

## Common Test Patterns

### Pattern 1: Simple Response Test

```python
@pytest.mark.asyncio
async def test_simple_response(self, agent_client, response_client):
    await agent_client.send_activity("Test message")
    responses = await response_client.pop()
    assert len(responses) > 0
```

### Pattern 2: Response Content Validation

```python
@pytest.mark.asyncio
async def test_response_content(self, agent_client, response_client):
    await agent_client.send_activity("Say hello")
    responses = await response_client.pop()
    assert responses[0].text == "Hello!"
```

### Pattern 3: Multiple Messages

```python
@pytest.mark.asyncio
async def test_conversation(self, agent_client, response_client):
    # First message
    await agent_client.send_activity("Hi")
    responses = await response_client.pop()
    assert len(responses) > 0
    
    # Second message
    await agent_client.send_activity("How are you?")
    responses = await response_client.pop()
    assert len(responses) > 0
```

### Pattern 4: With Expect Replies

```python
@pytest.mark.asyncio
async def test_with_expect_replies(self, agent_client):
    from microsoft_agents.activity import Activity
    
    activity = Activity(
        type="message",
        text="Question?"
    )
    
    # Send and wait for replies
    replies = await agent_client.send_expect_replies(activity)
    assert len(replies) > 0
```

## Troubleshooting Quick Fixes

### Issue: Connection Refused
```
Error: Connection refused at localhost:3978
```
**Solution**: Make sure your agent is running on port 3978

### Issue: Missing Environment Variables
```
Error: CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID not found
```
**Solution**: Create `.env` file with required credentials

### Issue: Import Error
```
ModuleNotFoundError: No module named 'microsoft_agents'
```
**Solution**: Run `pip install microsoft-agents-testing`

## Next Steps

Now that you have your first test running:

1. **Learn More**: Read [Integration Testing Guide](./INTEGRATION_TESTING.md)
2. **Advanced Testing**: Check [Data-Driven Testing Guide](./DATA_DRIVEN_TESTING.md)
3. **Run Benchmarks**: See [Performance Testing Guide](./PERFORMANCE_TESTING.md)
4. **Best Practices**: Review [Best Practices Guide](./BEST_PRACTICES.md)
5. **Full API**: Explore [API Reference](./API_REFERENCE.md)

## Useful Commands

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Run specific test class
pytest tests/test_agent.py::TestMyAgent -v

# Run with coverage
pytest tests/ --cov=.

# Run DDT tests
aclip --env_path .env ddt ./tests/scenarios.yaml -v

# Run benchmark
aclip --env_path .env benchmark -p ./payload.json -n 10

# Show all fixtures
pytest --fixtures tests/test_agent.py
```

## File Structure for Testing

Recommended project layout:

```
my_agent_project/
├── .env                          # Your credentials
├── agent/                        # Your agent code
│   ├── __init__.py
│   ├── app.py
│   └── handlers/
├── tests/                        # Test directory
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_agent.py            # Your tests
│   ├── test_scenarios.py        # More tests
│   └── scenarios.yaml           # DDT tests
└── pytest.ini                    # Pytest config
```

## Getting Help

- 📚 **Detailed Guides**: Check the `guides/` directory
- 🔍 **API Documentation**: See [API_REFERENCE.md](./API_REFERENCE.md)
- 🎯 **Examples**: Browse `samples/` directory
- 🐛 **Issues**: See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

**Ready for more?** Jump to [Integration Testing Guide](./INTEGRATION_TESTING.md) for deeper knowledge!

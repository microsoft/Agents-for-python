# Sample: Basic Agent Testing

A simple example of how to test a basic agent.

## Setup

1. Create test environment:
```bash
cd samples/basic_agent_testing
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install microsoft-agents-testing pytest pytest-asyncio
```

3. Create `.env`:
```bash
cat > .env << 'EOF'
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-secret
AGENT_URL=http://localhost:3978/
SERVICE_URL=http://localhost:8001/
EOF
```

## Run Tests

```bash
# Run all tests
pytest test_basic_agent.py -v

# Run specific test
pytest test_basic_agent.py::TestBasicAgent::test_greeting -v

# With output
pytest test_basic_agent.py -v -s
```

## Expected Output

```
test_basic_agent.py::TestBasicAgent::test_greeting PASSED
test_basic_agent.py::TestBasicAgent::test_question PASSED
test_basic_agent.py::TestBasicAgent::test_empty_message PASSED

====== 3 passed in 2.34s ======
```

## What This Sample Shows

✅ Basic test class structure  
✅ Sending activities  
✅ Receiving responses  
✅ Simple assertions  
✅ Error handling  

## Next Steps

- Modify tests to match your agent
- Add more test scenarios
- See [INTEGRATION_TESTING.md](../guides/INTEGRATION_TESTING.md) for advanced patterns

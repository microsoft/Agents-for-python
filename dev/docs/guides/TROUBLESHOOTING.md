# Troubleshooting Guide

Common issues and solutions for the Microsoft Agents Testing Framework.

## General Issues

### Installation Problems

#### Issue: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'microsoft_agents'
```

**Solutions**:
```bash
# Reinstall package
pip install --force-reinstall microsoft-agents-testing

# Verify installation
pip show microsoft-agents-testing

# Check Python version (need 3.10+)
python --version
```

#### Issue: Dependency Conflict
```
ERROR: pip's dependency resolver does not currently take into account...
```

**Solutions**:
```bash
# Create fresh virtual environment
python -m venv venv_fresh
source venv_fresh/bin/activate
pip install microsoft-agents-testing
```

## Configuration Issues

### Issue: Missing Environment File
```
FileNotFoundError: [Errno 2] No such file or directory: '.env'
```

**Solution**:
```bash
# Create .env file
cat > .env << 'EOF'
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-secret
EOF
```

### Issue: Invalid Environment Variables
```
KeyError: 'CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID'
```

**Solution**:
```bash
# Verify .env syntax
cat .env

# Check for typos in variable names
# Variable names are case-sensitive!
```

### Issue: Credentials Not Working
```
Unauthorized: Invalid credentials
```

**Solutions**:
1. Verify credentials in Azure Portal
2. Check if secret expired (generate new)
3. Verify tenant ID is correct
4. Ensure bot service exists

## Connection Issues

### Issue: Connection Refused
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solutions**:
```bash
# Check if agent is running
curl http://localhost:3978/

# Start agent
# (depends on your agent setup)

# Check if service running on correct port
netstat -an | grep 3978  # Windows: netstat -ano
```

### Issue: Timeout
```
asyncio.TimeoutError: Timeout waiting for response
```

**Solutions**:
```bash
# 1. Check agent is responding
curl http://localhost:3978/

# 2. Increase timeout in test
import asyncio

try:
    response = await asyncio.wait_for(
        response_client.pop(),
        timeout=10.0  # Increase from default
    )
except asyncio.TimeoutError:
    print("Agent too slow")

# 3. Check agent logs for errors
```

### Issue: Port Already in Use
```
OSError: [Errno 98] Address already in use
```

**Solutions**:
```bash
# Find process using port
lsof -i :8001  # macOS/Linux
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
aclip --env_path .env auth --port 9999
```

## Test Execution Issues

### Issue: No Tests Discovered
```
ERROR: not found: /<path>/tests/ (no tests ran)
```

**Solutions**:
```bash
# Check file naming
# Must be: test_*.py or *_test.py

# Rename file
mv my_tests.py test_my_tests.py

# Run with discovery
pytest --collect-only tests/
```

### Issue: Async Test Fails
```
RuntimeError: no running event loop
```

**Solutions**:
```python
# Ensure decorator is present
@pytest.mark.asyncio  # Don't forget this!
async def test_something(self):
    pass

# Check pytest.ini
# asyncio_mode = auto

# Or use fixture
@pytest.fixture
async def async_test():
    await setup()
    yield
    await cleanup()
```

### Issue: Fixture Not Found
```
fixture 'agent_client' not found
```

**Solutions**:
```bash
# Check conftest.py exists
ls tests/conftest.py

# Show available fixtures
pytest --fixtures tests/test_file.py

# Ensure fixture defined in Integration or conftest
```

## Response Issues

### Issue: No Responses Received
```
AssertionError: assert 0 > 0
```

**Debugging**:
```python
@pytest.mark.asyncio
async def test_debug(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    
    # Wait a bit for response
    import asyncio
    await asyncio.sleep(1.0)
    
    responses = await response_client.pop()
    print(f"Responses: {responses}")
    print(f"Count: {len(responses)}")
    
    assert len(responses) > 0
```

**Check**:
1. Agent is running
2. Service URL is correct
3. Conversation ID is valid
4. Wait time is sufficient

### Issue: Empty Response Text
```
AssertionError: assert '' is not None
```

**Solution**:
```python
# Check if response exists before accessing text
if responses and responses[0].text:
    assert "Expected" in responses[0].text
else:
    print("No text in response")
```

## CLI Issues

### Issue: aclip Command Not Found
```
aclip: command not found
```

**Solutions**:
```bash
# Verify installation
pip install microsoft-agents-testing

# Try direct module
python -m microsoft_agents.testing.cli --help

# Check if in PATH
which aclip

# Or use with python -m
python -m microsoft_agents.testing.cli ddt test.yaml
```

### Issue: Invalid YAML File
```
yaml.scanner.ScannerError: mapping values are not allowed
```

**Solution**:
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('test.yaml'))"

# Check indentation (must be 2 spaces)
# Use YAML validator online
```

### Issue: Payload File Missing
```
FileNotFoundError: [Errno 2] No such file or directory: 'payload.json'
```

**Solution**:
```bash
# Create payload file
cat > payload.json << 'EOF'
{
  "type": "message",
  "text": "Hello"
}
EOF

# Or specify full path
aclip --env_path .env post -p /full/path/payload.json
```

## Performance Issues

### Issue: Benchmark Times Out
```
TimeoutError: Operation timed out
```

**Solution**:
```bash
# Reduce number of workers
aclip --env_path .env benchmark -p payload.json -n 5

# Check agent performance
# May be too slow for high concurrency
```

### Issue: Memory Usage Grows
```
MemoryError: Unable to allocate memory
```

**Solution**:
```bash
# Reduce workers
aclip benchmark -p payload.json -n 10

# Close connections properly
await client.close()

# Monitor memory
# Use profiling tools
```

## Data-Driven Testing Issues

### Issue: Assertion Not Found
```
AssertionError: Key 'path' not in response
```

**Solution**:
```yaml
# Check the actual response structure
# Use verbose mode to see responses
# Correct the path in YAML
```

### Issue: Type Mismatch
```
TypeError: Cannot compare string with int
```

**Solution**:
```yaml
# Ensure value type matches field type
# String comparison: contains, equals
# Numeric comparison: greater_than, less_than
```

## Debugging Strategies

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.mark.asyncio
async def test_with_debug(self, agent_client, response_client):
    logger = logging.getLogger(__name__)
    logger.debug("Starting test")
    # ... test code ...
```

Run with output:
```bash
pytest tests/ -v -s
```

### Print Debugging

```python
@pytest.mark.asyncio
async def test_debug(self, agent_client, response_client):
    print("\n=== Debug Info ===")
    
    await agent_client.send_activity("Hello")
    print(f"Activity sent")
    
    responses = await response_client.pop()
    print(f"Response count: {len(responses)}")
    
    for i, resp in enumerate(responses):
        print(f"Response {i}:")
        print(f"  Type: {resp.type}")
        print(f"  Text: {resp.text}")
        print(f"  From: {getattr(resp, 'from', 'Unknown')}")
```

### Use pdb Debugger

```python
@pytest.mark.asyncio
async def test_with_pdb(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    
    import pdb; pdb.set_trace()
    # Debugger pauses here
    # Use: n (next), c (continue), p (print), etc.
```

## Getting Help

### Resources

- **Documentation**: Check [../](../)
- **Examples**: See [samples/](../samples/)
- **Issues**: Create issue on GitHub
- **Stack Overflow**: Tag with `microsoft-agents`

### Creating Good Bug Reports

Include:
1. Minimal reproducible example
2. Error message and stack trace
3. Python version (`python --version`)
4. Package version (`pip show microsoft-agents-testing`)
5. Environment (Windows/Mac/Linux)
6. Steps to reproduce

### Minimal Reproducible Example

```python
import pytest
from microsoft_agents.testing import Integration

class TestMinimal(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_issue(self, agent_client, response_client):
        # Minimal code that shows the issue
        await agent_client.send_activity("Hello")
        responses = await response_client.pop()
        # What's wrong?
```

## Performance Optimization

### Slow Tests

```python
# Add timeout
@pytest.mark.timeout(5)  # 5 second limit
def test_quick():
    pass

# Mark as slow to skip
@pytest.mark.slow
def test_slow():
    pass

# Run without slow tests
pytest tests/ -m "not slow"
```

### Optimize Async Code

```python
# ✓ Good - parallel
import asyncio
tasks = [
    client.send_activity(f"Msg {i}")
    for i in range(10)
]
await asyncio.gather(*tasks)

# ✗ Slow - sequential
for i in range(10):
    await client.send_activity(f"Msg {i}")
```

---

**Need more help?** Review the [Best Practices Guide](./BEST_PRACTICES.md) or check the main [documentation](../).

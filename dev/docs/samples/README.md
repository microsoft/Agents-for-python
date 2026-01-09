# Sample Tests & Examples

This directory contains practical examples of using the Microsoft Agents Testing Framework.

## Samples Overview

### 1. Basic Agent Testing
**Location**: `basic_agent_testing/`

A complete working example showing:
- Simple test class structure
- Sending activities
- Receiving responses
- Basic assertions
- Error handling

**Run**:
```bash
cd basic_agent_testing
pytest test_basic_agent.py -v
```

**See Also**: [INTEGRATION_TESTING.md](../guides/INTEGRATION_TESTING.md)

---

### 2. Data-Driven Testing
**Location**: `data_driven_testing/`

Examples of YAML-based declarative testing:
- Greeting scenarios
- Question scenarios
- Error handling scenarios

**Files**:
- `greetings.yaml` - Greeting test patterns
- `error_handling.yaml` - Error case testing

**Run**:
```bash
aclip --env_path ../../.env ddt greetings.yaml -v
```

**See Also**: [DATA_DRIVEN_TESTING.md](../guides/DATA_DRIVEN_TESTING.md)

---

### 3. Performance Benchmarking
**Location**: `performance_benchmarking/`

Learn to benchmark your agent:
- Simple load testing
- Progressive load testing
- Async benchmarking
- Payload comparison

**Payloads**:
- `payload_simple.json` - Basic message
- `payload_complex.json` - Complex message

**Run**:
```bash
aclip --env_path ../../.env benchmark -p payload_simple.json -n 10 -v
```

**See Also**: [PERFORMANCE_TESTING.md](../guides/PERFORMANCE_TESTING.md)

---

## Quick Start with Samples

### Option 1: Use Basic Example

1. Copy `basic_agent_testing` to your project
2. Update `.env` with your credentials
3. Start your agent
4. Run tests:
   ```bash
   pytest test_basic_agent.py -v
   ```

### Option 2: Use Data-Driven Example

1. Copy YAML files from `data_driven_testing`
2. Customize scenarios for your agent
3. Run via CLI:
   ```bash
   aclip --env_path .env ddt greetings.yaml -v
   ```

### Option 3: Performance Testing

1. Create your payload JSON
2. Run benchmark:
   ```bash
   aclip --env_path .env benchmark -p payload.json -n 10
   ```

## Sample File Structure

```
samples/
├── basic_agent_testing/              # Python-based tests
│   ├── README.md
│   ├── test_basic_agent.py          # Test class
│   └── conftest.py                   # (optional) Shared fixtures
│
├── data_driven_testing/              # YAML-based tests
│   ├── README.md
│   ├── greetings.yaml               # Greeting scenarios
│   ├── questions.yaml               # Q&A scenarios
│   └── error_handling.yaml          # Error cases
│
├── performance_benchmarking/         # Benchmark examples
│   ├── README.md
│   ├── payload_simple.json          # Simple message
│   └── payload_complex.json         # Complex message
│
└── README.md                         # This file
```

## Common Tasks

### Task 1: Add New Test Scenario

**Python**: Add method to test class
```python
@pytest.mark.asyncio
async def test_new_scenario(self, agent_client, response_client):
    await agent_client.send_activity("New test")
    responses = await response_client.pop()
    assert len(responses) > 0
```

**YAML**: Add scenario to YAML file
```yaml
- name: "New Scenario"
  send:
    type: "message"
    text: "Test"
  assert:
    - type: "exists"
      path: "text"
```

### Task 2: Test Different Agent Response

Python: Modify test
```python
await agent_client.send_activity("Different message")
```

YAML: Modify `send` section
```yaml
send:
  type: "message"
  text: "Different message"
```

### Task 3: Performance Baseline

```bash
# Run baseline
aclip --env_path .env benchmark -p payload.json -n 50 > baseline.txt

# Later, compare
aclip --env_path .env benchmark -p payload.json -n 50 > current.txt

# Diff results
diff baseline.txt current.txt
```

## Best Practices

✅ **DO**:
- Start with basic sample
- Customize for your agent
- Keep tests focused
- Use meaningful names
- Test error cases

❌ **DON'T**:
- Copy tests without understanding
- Leave placeholder values in code
- Test unrelated scenarios in one test
- Ignore failures

## Next Steps

1. **Start Here**: [Quick Start Guide](../guides/QUICK_START.md)
2. **Python Tests**: [Integration Testing](../guides/INTEGRATION_TESTING.md)
3. **YAML Tests**: [Data-Driven Testing](../guides/DATA_DRIVEN_TESTING.md)
4. **Performance**: [Performance Testing](../guides/PERFORMANCE_TESTING.md)
5. **Best Practices**: [Best Practices Guide](../guides/BEST_PRACTICES.md)

## Troubleshooting

### Tests Not Running
- Check `.env` exists with valid credentials
- Ensure agent is running
- Verify Python version is 3.10+

### YAML Tests Fail
- Validate YAML syntax
- Check assertion types match response structure
- Use `-v` flag for verbose output

### Performance Tests Timeout
- Check agent is responding quickly
- Reduce worker count
- Increase timeout values

See [TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) for more help.

## Getting Help

- 📖 **Guides**: Read [../guides/](../guides/)
- 🔍 **API Docs**: See [../guides/API_REFERENCE.md](../guides/API_REFERENCE.md)
- 🐛 **Issues**: Check [TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md)
- 💬 **Questions**: Create GitHub issue

---

**Ready to test?** Pick a sample and get started!

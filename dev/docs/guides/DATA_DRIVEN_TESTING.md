# Data-Driven Testing Guide

Master YAML-based declarative testing for Microsoft Agents.

## Introduction

Data-Driven Testing (DDT) separates test logic from test data using YAML files. This approach:
- Makes tests readable for non-technical people
- Reduces code duplication
- Simplifies test maintenance
- Enables rapid test creation

## YAML Test File Structure

### Basic Structure

```yaml
name: "Test Suite Name"
description: "Optional description"

scenarios:
  - name: "Scenario 1"
    send: {...}
    assert: [...]
  
  - name: "Scenario 2"
    send: {...}
    assert: [...]
```

### Minimal Example

```yaml
name: "Greeting Tests"

scenarios:
  - name: "Simple Greeting"
    send:
      type: "message"
      text: "Hello"
    assert:
      - type: "exists"
        path: "text"
```

## Send Activity Definition

### Activity Types

#### Message Activity

```yaml
send:
  type: "message"
  text: "Hello agent!"
  from: "user@example.com"
  locale: "en-US"
  channelId: "directline"
```

#### Invoke Activity

```yaml
send:
  type: "invoke"
  name: "custom_action"
  value:
    param1: "value1"
    param2: "value2"
```

#### Custom Activity

```yaml
send:
  type: "message"
  text: "Test"
  from: "user123"
  conversation: "conv123"
  timestamp: "2024-01-07T10:00:00Z"
  additionalField: "value"
```

## Assertion Types

### 1. Exists Assertion

Check field exists (regardless of value):

```yaml
assert:
  - type: "exists"
    path: "text"  # Check response.text exists
```

### 2. Not Exists Assertion

Check field does NOT exist:

```yaml
assert:
  - type: "not_exists"
    path: "error"
```

### 3. Equals Assertion

Check exact value:

```yaml
assert:
  - type: "equals"
    path: "text"
    value: "Hello!"
```

### 4. Contains Assertion

Check contains substring:

```yaml
assert:
  - type: "contains"
    path: "text"
    value: "Hello"
```

### 5. Greater Than / Less Than

```yaml
assert:
  - type: "greater_than"
    path: "length"
    value: 5
  
  - type: "less_than"
    path: "duration"
    value: 1000
```

## Complete YAML Examples

### Example 1: Simple Greeting Tests

```yaml
name: "Greeting Scenarios"
description: "Test various greeting patterns"

scenarios:
  - name: "Formal Greeting"
    send:
      type: "message"
      text: "Good morning"
    assert:
      - type: "exists"
        path: "text"
      - type: "contains"
        path: "text"
        value: "morning"
  
  - name: "Casual Greeting"
    send:
      type: "message"
      text: "Hey there!"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Multi-language"
    send:
      type: "message"
      text: "Hola"
      locale: "es-ES"
    assert:
      - type: "exists"
        path: "text"
```

### Example 2: Question Answering

```yaml
name: "QA Scenarios"

scenarios:
  - name: "Math Question"
    send:
      type: "message"
      text: "What is 2 + 2?"
    assert:
      - type: "contains"
        path: "text"
        value: "4"
  
  - name: "Knowledge Question"
    send:
      type: "message"
      text: "What's the capital of France?"
    assert:
      - type: "contains"
        path: "text"
        value: "Paris"
  
  - name: "Unknown Question"
    send:
      type: "message"
      text: "Random nonsense xyz123"
    assert:
      - type: "exists"
        path: "text"  # Should still respond
```

### Example 3: Error Handling

```yaml
name: "Error Handling"

scenarios:
  - name: "Empty Message"
    send:
      type: "message"
      text: ""
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Very Long Message"
    send:
      type: "message"
      text: "This is a very long message that contains many words and is designed to test how the agent handles long input..."
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Special Characters"
    send:
      type: "message"
      text: "!@#$%^&*()_+-=[]{}|;:',.<>?/"
    assert:
      - type: "exists"
        path: "text"
```

### Example 4: Advanced Scenarios

```yaml
name: "Advanced Testing"

scenarios:
  - name: "With User Info"
    send:
      type: "message"
      text: "Hello"
      from:
        id: "user123"
        name: "Alice"
      conversation:
        id: "conv456"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "With Locale"
    send:
      type: "message"
      text: "Bonjour"
      locale: "fr-FR"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Invoke Action"
    send:
      type: "invoke"
      name: "get_weather"
      value:
        city: "Seattle"
        units: "metric"
    assert:
      - type: "exists"
        path: "value"
```

## Running DDT Tests

### Command Line

```bash
# Run single YAML file
aclip --env_path .env ddt ./tests/scenarios.yaml

# With verbose output
aclip --env_path .env ddt ./tests/scenarios.yaml -v

# With custom pytest args
aclip --env_path .env ddt ./tests/scenarios.yaml --pytest-args "-v -s"
```

### Multiple Files

```bash
# Run all YAML files in directory
for file in tests/*.yaml; do
  aclip --env_path .env ddt "$file" -v
done
```

## File Organization

### Recommended Structure

```
tests/
├── ddt/                          # DDT YAML tests
│   ├── greeting.yaml            # Greeting scenarios
│   ├── questions.yaml           # QA scenarios
│   ├── error_handling.yaml      # Error cases
│   └── advanced.yaml            # Complex scenarios
│
├── fixtures/                     # Shared test data
│   └── sample_payloads.json
│
└── test_integration.py          # Python tests
```

### Running All DDT Tests

```bash
#!/bin/bash
# run_all_ddt_tests.sh

for yaml_file in tests/ddt/*.yaml; do
  echo "Running: $yaml_file"
  aclip --env_path .env ddt "$yaml_file" -v
done
```

## Best Practices

### 1. Descriptive Names

```yaml
# ✓ Good - clear intent
scenarios:
  - name: "Greeting responds with acknowledgement"
  - name: "Question about math returns numeric answer"
  - name: "Empty input triggers clarification request"

# ✗ Poor - vague
scenarios:
  - name: "Test 1"
  - name: "Scenario A"
  - name: "Check response"
```

### 2. One Assertion Type Per Scenario

When possible, keep scenarios focused:

```yaml
# ✓ Good - focused
scenarios:
  - name: "Response exists"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Response contains keyword"
    assert:
      - type: "contains"
        path: "text"
        value: "keyword"

# ✓ OK - related assertions
scenarios:
  - name: "Valid greeting response"
    assert:
      - type: "exists"
        path: "text"
      - type: "contains"
        path: "text"
        value: "Hello"
```

### 3. Organize by Category

```yaml
name: "Comprehensive Agent Tests"

# Group by feature
scenarios:
  # ===== Greetings =====
  - name: "Respond to hello"
    send: ...
  
  - name: "Respond to hi"
    send: ...
  
  # ===== Questions =====
  - name: "Answer math question"
    send: ...
  
  - name: "Answer knowledge question"
    send: ...
  
  # ===== Error Cases =====
  - name: "Handle empty message"
    send: ...
```

### 4. Use Meaningful Locales

```yaml
scenarios:
  - name: "English greeting"
    send:
      type: "message"
      text: "Hello"
      locale: "en-US"
  
  - name: "Spanish greeting"
    send:
      type: "message"
      text: "Hola"
      locale: "es-ES"
  
  - name: "French greeting"
    send:
      type: "message"
      text: "Bonjour"
      locale: "fr-FR"
```

## Advanced Patterns

### Parameterized Testing

While YAML DDT is declarative, you can still create multiple similar tests:

```yaml
name: "Multi-language Greetings"

scenarios:
  - name: "English greeting"
    send:
      type: "message"
      text: "Hello"
      locale: "en-US"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Spanish greeting"
    send:
      type: "message"
      text: "Hola"
      locale: "es-ES"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "French greeting"
    send:
      type: "message"
      text: "Bonjour"
      locale: "fr-FR"
    assert:
      - type: "exists"
        path: "text"
```

### Conditional Scenarios

Group related scenarios:

```yaml
name: "Conversation Flow"

scenarios:
  # Part 1: Greeting
  - name: "Step 1: Agent greets user"
    send:
      type: "message"
      text: "Hello"
    assert:
      - type: "exists"
        path: "text"
  
  # Part 2: Question
  - name: "Step 2: User asks question"
    send:
      type: "message"
      text: "How can you help?"
    assert:
      - type: "exists"
        path: "text"
  
  # Part 3: Goodbye
  - name: "Step 3: User says goodbye"
    send:
      type: "message"
      text: "Goodbye"
    assert:
      - type: "exists"
        path: "text"
```

## Converting Python Tests to DDT

### Python Test

```python
@pytest.mark.asyncio
async def test_greeting(self, agent_client, response_client):
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    assert len(responses) > 0
    assert "Hello" in responses[0].text or "Hi" in responses[0].text
```

### Equivalent YAML DDT

```yaml
name: "Greeting Test"

scenarios:
  - name: "Agent responds to greeting"
    send:
      type: "message"
      text: "Hello"
    assert:
      - type: "exists"
        path: "text"
      - type: "contains"
        path: "text"
        value: "Hello"
```

## Troubleshooting DDT

### Issue: YAML Syntax Error

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solution**: Check YAML indentation and syntax
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('test.yaml'))"
```

### Issue: Path Not Found

```
AssertionError: Path 'text' not found in response
```

**Solution**: Check the actual response structure
```bash
# Debug with verbose output
aclip --env_path .env ddt test.yaml -v -s
```

### Issue: Multiple Assertion Failures

Ensure assertions match actual response structure:

```yaml
# Check what fields are available
- type: "exists"
  path: "text"     # Is this field in response?
- type: "exists"
  path: "type"     # Or this?
```

## Complete DDT Test Suite

```yaml
name: "Complete Agent Test Suite"
description: "Comprehensive DDT test scenarios"

scenarios:
  # Greetings
  - name: "Greeting - Hello"
    send:
      type: "message"
      text: "Hello"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Greeting - Hi"
    send:
      type: "message"
      text: "Hi"
    assert:
      - type: "exists"
        path: "text"
  
  # Questions
  - name: "Question - Math"
    send:
      type: "message"
      text: "What is 5 + 3?"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Question - General"
    send:
      type: "message"
      text: "Tell me about yourself"
    assert:
      - type: "exists"
        path: "text"
  
  # Error Cases
  - name: "Error - Empty message"
    send:
      type: "message"
      text: ""
    assert:
      - type: "exists"
        path: "text"
  
  # Advanced
  - name: "Advanced - With user info"
    send:
      type: "message"
      text: "Hi"
      from:
        id: "user123"
        name: "Test User"
    assert:
      - type: "exists"
        path: "text"
```

## Summary

DDT Benefits:
✅ Readable format for non-technical users  
✅ Quick test creation  
✅ Easy maintenance  
✅ Decoupled logic from data  
✅ CLI execution  

When to use DDT:
- Simple acceptance tests
- Scenarios for stakeholders
- High volume of similar tests
- Non-technical team members write tests

---

**Related Guides**:
- [CLI Tools](./CLI_TOOLS.md) - DDT command details
- [Integration Testing](./INTEGRATION_TESTING.md) - Python-based tests
- [Best Practices](./BEST_PRACTICES.md) - Testing patterns

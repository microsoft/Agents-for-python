# Sample: Advanced Testing Patterns

Real-world advanced testing patterns for complex agent scenarios.

## Contents

1. **test_advanced_patterns.py** - Complex test scenarios
2. **conftest.py** - Shared fixtures and setup
3. **README.md** - This file

## Advanced Patterns Covered

✅ Multi-turn conversations  
✅ Context preservation  
✅ Custom fixtures  
✅ Error recovery  
✅ Performance assertions  
✅ Parameterized testing  
✅ Mock data handling  

## Running Tests

```bash
# Run all advanced tests
pytest test_advanced_patterns.py -v

# Run specific pattern
pytest test_advanced_patterns.py::TestAdvancedPatterns::test_multi_turn_conversation -v

# With verbose output
pytest test_advanced_patterns.py -v -s
```

## Key Concepts

### 1. Custom Fixtures

```python
@pytest.fixture
def conversation_data():
    return {
        "greeting": "Hello",
        "name": "Alice",
        "question": "How can you help?"
    }
```

### 2. Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("Hi", "Hello"),
    ("Hey", "Hi"),
])
def test_greetings(self, input, expected):
    pass
```

### 3. Mock Data

```python
@pytest.fixture
def mock_responses():
    return {
        "greeting": "Hello! How can I help?",
        "error": "I didn't understand that."
    }
```

## See Also

- [BEST_PRACTICES.md](../../guides/BEST_PRACTICES.md)
- [INTEGRATION_TESTING.md](../../guides/INTEGRATION_TESTING.md)
- [Performance Testing](../performance_benchmarking/)

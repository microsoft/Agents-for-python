# Microsoft Agents Testing Framework - Comprehensive Guide

## Overview

The Microsoft Agents Testing Framework is a powerful, feature-rich testing toolkit designed to help developers build robust, reliable agents using the Microsoft Agents SDK. Whether you're writing unit tests, integration tests, or running performance benchmarks, this framework provides the tools you need.

## Table of Contents

1. [Quick Start Guide](./guides/QUICK_START.md) - Get up and running in 5 minutes
2. [Installation & Setup](./guides/INSTALLATION.md) - Complete installation instructions
3. [Core Components](./guides/CORE_COMPONENTS.md) - Understand the framework's main building blocks
4. [Integration Testing](./guides/INTEGRATION_TESTING.md) - Write comprehensive integration tests
5. [Data-Driven Testing (DDT)](./guides/DATA_DRIVEN_TESTING.md) - Use YAML for declarative testing
6. [CLI Tools](./guides/CLI_TOOLS.md) - Master the command-line interface
7. [Assertions & Validation](./guides/ASSERTIONS.md) - Advanced assertion patterns
8. [Authentication](./guides/AUTHENTICATION.md) - Handle Azure Bot Service auth
9. [Performance Testing](./guides/PERFORMANCE_TESTING.md) - Benchmark your agents
10. [API Reference](./guides/API_REFERENCE.md) - Complete API documentation
11. [Best Practices](./guides/BEST_PRACTICES.md) - Testing patterns and recommendations
12. [Troubleshooting](./guides/TROUBLESHOOTING.md) - Common issues and solutions

## Key Features

### 🧪 Integration Testing Framework
Full-featured integration testing with pytest support for testing agents in realistic scenarios.

### 📊 Data-Driven Testing (DDT)
YAML-based declarative testing approach that separates test logic from test data.

### ✅ Advanced Assertions
Sophisticated assertion framework with model queries, field validation, and flexible quantifiers.

### 🔐 Authentication Helpers
Built-in utilities for OAuth token generation and Azure Bot Service authentication.

### 🚀 CLI Tools
Powerful command-line interface with utilities for testing, benchmarking, and diagnostics.

### 📈 Performance Benchmarking
Load testing capabilities with concurrent workers for performance analysis.

### 🎭 Mock Services
Built-in mock response service for testing agent responses without external dependencies.

## Getting Started

### Installation

```bash
pip install microsoft-agents-testing
```

### Minimal Example

```python
import pytest
from microsoft_agents.testing import Integration, AgentClient, ResponseClient

class TestMyAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"

    @pytest.mark.asyncio
    async def test_hello_world(self, agent_client: AgentClient, response_client: ResponseClient):
        # Send a message
        await agent_client.send_activity("Hello!")
        
        # Get responses
        responses = await response_client.pop()
        
        # Assert
        assert len(responses) > 0
```

## Framework Architecture

### Component Hierarchy

```
Testing Framework
├── Integration Base Class
│   ├── Agent Client (sends activities)
│   ├── Response Client (receives responses)
│   ├── Environment (manages test setup)
│   └── Sample (your agent app)
├── Assertions Engine
│   ├── Field Assertions
│   ├── Model Assertions
│   └── Quantifiers
├── Data-Driven Testing
│   ├── YAML Parser
│   ├── Test Runner
│   └── Activity Builder
├── CLI Tools
│   ├── DDT Runner
│   ├── Authentication Server
│   ├── Benchmark Tool
│   └── Activity Poster
└── Utilities
    ├── Configuration (SDKConfig)
    ├── Token Generation
    ├── Activity Helpers
    └── Async Helpers
```

## Common Use Cases

### Use Case 1: Testing Agent Responses
Test that your agent responds correctly to user messages. See [Integration Testing Guide](./guides/INTEGRATION_TESTING.md).

### Use Case 2: Declarative Test Suites
Define tests in YAML for non-technical team members. See [Data-Driven Testing Guide](./guides/DATA_DRIVEN_TESTING.md).

### Use Case 3: Performance Validation
Ensure your agent meets performance requirements under load. See [Performance Testing Guide](./guides/PERFORMANCE_TESTING.md).

### Use Case 4: Multi-Agent Coordination
Test complex interactions between multiple agents. See [Advanced Patterns](./guides/BEST_PRACTICES.md#multi-agent-patterns).

## Sample Projects

Explore practical examples in the [samples directory](./samples/):

- **Basic Agent Testing** - Simple hello-world agent test
- **Complex Conversation Flow** - Multi-turn conversation testing
- **Data-Driven Tests** - YAML-based test scenarios
- **Performance Benchmarks** - Load testing examples
- **Custom Assertions** - Advanced validation patterns

## Testing Workflow

### Typical Development Cycle

1. **Define Test Case** - Write your test in YAML or Python
2. **Setup Environment** - Configure agent and authentication
3. **Run Test** - Execute using pytest or CLI
4. **Validate Results** - Check assertions pass
5. **Benchmark** - Measure performance if needed

### Development Environment Setup

1. Clone your agent project
2. Install testing framework
3. Create `.env` with credentials
4. Create `tests/` directory
5. Write your first test
6. Run with `pytest` or `aclip` CLI

## Support & Resources

- **Documentation**: See individual guides in [./guides/](./guides/)
- **Examples**: Check [./samples/](./samples/) directory
- **API Reference**: [API_REFERENCE.md](./guides/API_REFERENCE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)
- **GitHub Issues**: [Report issues](https://github.com/microsoft/Agents)

## Next Steps

1. **New to the framework?** Start with [Quick Start Guide](./guides/QUICK_START.md)
2. **Want integration tests?** See [Integration Testing Guide](./guides/INTEGRATION_TESTING.md)
3. **Prefer YAML-based tests?** Check [Data-Driven Testing Guide](./guides/DATA_DRIVEN_TESTING.md)
4. **Need to benchmark?** Read [Performance Testing Guide](./guides/PERFORMANCE_TESTING.md)
5. **Looking for best practices?** Review [Best Practices Guide](./guides/BEST_PRACTICES.md)

## Framework Statistics

| Component | Lines of Code | Test Coverage |
|-----------|---------------|----------------|
| Integration Testing | ~1,000 | High |
| Assertions Engine | ~800 | High |
| Data-Driven Testing | ~600 | High |
| CLI Tools | ~1,200 | Medium |
| Utilities | ~400 | High |

## Version & Compatibility

- **Framework Version**: 1.0+
- **Python**: 3.10+
- **Microsoft Agents SDK**: Latest
- **Pytest**: 7.0+

## License

MIT License - See LICENSE file for details

---

**Get started now**: Head to [Quick Start Guide](./guides/QUICK_START.md) to run your first test!

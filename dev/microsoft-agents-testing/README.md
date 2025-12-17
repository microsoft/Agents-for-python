# microsoft-agents-testing

A comprehensive testing framework for Microsoft Agents in Python. This package provides powerful tools for integration testing, data-driven testing, assertion helpers, authentication utilities, and performance benchmarking for agents built with the Microsoft Agents SDK.

## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
  - [Integration Testing](#integration-testing)
  - [Data-Driven Testing (DDT)](#data-driven-testing-ddt)
  - [Assertions](#assertions)
  - [Authentication](#authentication)
  - [SDK Configuration](#sdk-configuration)
- [CLI Tools](#cli-tools)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Future Goals](#future-goals)
- [Contributing](#contributing)

## Installation

### Standard Installation

```bash
pip install microsoft-agents-testing
```

### Development Installation (Editable Mode)

For active development:

```bash
pip install -e ./microsoft-agents-testing/ --config-settings editable_mode=compat
```

### Requirements

- Python >= 3.10
- Dependencies:
  - `microsoft-agents-activity`
  - `microsoft-agents-hosting-core`
  - `microsoft-agents-authentication-msal`
  - `microsoft-agents-hosting-aiohttp`
  - `pyjwt>=2.10.1`
  - `isodate>=0.6.1`
  - `azure-core>=1.30.0`
  - `python-dotenv>=1.1.1`

## Features

✅ **Integration Testing Framework** - Full-featured integration testing with pytest support  
✅ **Data-Driven Testing** - YAML-based test definitions for declarative testing  
✅ **Flexible Assertions** - Advanced model and field assertion capabilities  
✅ **Authentication Helpers** - OAuth token generation for Azure Bot Service  
✅ **CLI Tools** - Command-line interface for testing and benchmarking  
✅ **Performance Benchmarking** - Load testing with concurrent workers  
✅ **Response Mocking** - Built-in mock service for testing agent responses  
✅ **Activity Utilities** - Helper functions for activity manipulation

## Quick Start

### 1. Set Up Environment

Create a `.env` file with your Azure Bot Service credentials:

```env
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-client-secret
```

### 2. Basic Integration Test

```python
import pytest
from microsoft_agents.testing import Integration, ddt

@ddt("tests/my_agent/directline")
class TestMyAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
```

### 3. Run Data-Driven Tests via CLI

```bash
aclip --env_path .env ddt ./tests/my_test.yaml
```

### 4. Generate Authentication Token

```python
from microsoft_agents.testing import generate_token

token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant-id"
)
```

## Core Components

### Integration Testing

The `Integration` class provides a complete pytest-based integration testing framework with fixtures for environment setup, agent clients, and response handling.

#### Key Features:
- Automatic environment initialization
- Agent client management with authentication
- Response client for mocking service endpoints
- Configurable service and agent URLs
- Support for multiple test environments

#### Example:

```python
import pytest
from microsoft_agents.testing import Integration, ddt

@ddt("tests/basic_agent/directline", prefix="directline")
class TestBasicAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = "agents/basic_agent/.env"
    
    # Tests are automatically generated from YAML files
```

### Data-Driven Testing (DDT)

Data-driven testing allows you to define test scenarios in YAML files, making tests declarative, maintainable, and easy to understand.

#### YAML Test Structure:

```yaml
name: SendActivity_ConversationUpdate_ReturnsWelcomeMessage
description: Tests that a conversation update activity triggers a welcome message

defaults:
  input:
    activity:
      channelId: directline
      locale: en-US
  assertion:
    quantifier: all

test:
  - type: input
    activity:
      type: conversationUpdate
      from:
        id: user1
      conversation:
        id: conversation-001
      membersAdded:
        - id: bot@serviceurl
          name: bot
        - id: user1
  
  - type: assertion
    selector:
      index: -1
    activity:
      type: message
      text: ["CONTAINS", "Hello and Welcome!"]
```

#### Test Step Types:

- **`input`** - Send an activity to the agent
- **`assertion`** - Assert expected responses
- **`sleep`** - Wait for a specified duration
- **`breakpoint`** - Trigger a debugger breakpoint
- **`skip`** - Skip the current step

#### Defaults System:

You can define defaults for inputs, assertions, and sleep durations to reduce repetition:

```yaml
defaults:
  input:
    activity:
      channelId: directline
      locale: en-US
      textFormat: plain
  assertion:
    quantifier: all
  sleep:
    duration: 0.5
```

#### Parent/Child Test Inheritance:

Tests can inherit defaults from parent test files:

```yaml
parent: _parent.yaml

name: ChildTest
test:
  - type: input
    activity:
      text: "Hello"
```

### Assertions

Powerful assertion system for validating agent responses with support for nested object validation and flexible matching.

#### Field Assertions

```python
from microsoft_agents.testing import assert_field, FieldAssertionType

# Exact match
assert_field(activity.text, "Hello", FieldAssertionType.EQUALS)

# Contains check
assert_field(activity.text, "Hello", FieldAssertionType.CONTAINS)

# Exists check
assert_field(activity.text, None, FieldAssertionType.EXISTS)
```

#### Model Assertions

```python
from microsoft_agents.testing import assert_model, ModelAssertion
from microsoft_agents.activity import Activity

# Simple assertion
expected = Activity(type="message", text="Hello")
assert_model(actual_activity, expected)

# Advanced assertion with selector
assertion = ModelAssertion(
    assertion={"type": "message", "text": ["CONTAINS", "Hello"]},
    selector=ModelSelector(index=-1),
    quantifier=AssertionQuantifier.ALL
)

# Check multiple activities
passes, error = assertion.check(activity_list)
assert passes, error
```

#### Assertion Quantifiers:

- **`ALL`** - All selected items must match
- **`ONE`** - Exactly one item must match
- **`NONE`** - No items should match

#### Model Selector:

```python
from microsoft_agents.testing import ModelSelector

# Select by index
selector = ModelSelector(index=-1)  # Last item

# Select by model properties
selector = ModelSelector(model={"type": "message"})

# Select first match
first_match = selector.select_first(activities)
```

### Authentication

Generate OAuth tokens for testing against Azure Bot Service.

```python
from microsoft_agents.testing import generate_token, generate_token_from_config
from microsoft_agents.testing import SDKConfig

# Direct token generation
token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant-id"
)

# Token from configuration
config = SDKConfig(env_path=".env")
token = generate_token_from_config(config)
```

### SDK Configuration

The `SDKConfig` class loads and provides access to SDK configuration from `.env` files or environment variables.

```python
from microsoft_agents.testing import SDKConfig

# Load configuration
config = SDKConfig(env_path=".env")

# Get connection settings
connection = config.get_connection("SERVICE_CONNECTION")

# Access configuration dictionary
config_dict = config.config
```

## CLI Tools

The package includes a powerful CLI tool accessible via the `aclip` command.

### Available Commands

#### 1. Data-Driven Testing

Run data-driven tests from YAML files:

```bash
aclip --env_path .env ddt ./tests/my_test.yaml --service_url http://localhost:8001/
```

Options:
- `--env_path` - Path to environment file (default: `.env`)
- `--service_url` - Service URL for responses (default: `http://localhost:8001/`)
- `--pytest-args` - Arguments to pass to pytest (default: `-v -s`)

#### 2. Authentication Test Server

Run a test authentication server:

```bash
aclip --env_path .env auth --port 3978
```

Options:
- `--port` - Port to run the server on (default: `3978`)

#### 3. Post Activity

Send a single activity to an agent:

```bash
aclip --env_path .env post --payload_path ./payload.json
```

Options:
- `--payload_path` / `-p` - Path to payload JSON file (default: `./payload.json`)
- `--verbose` / `-v` - Enable verbose logging
- `--async_mode` / `-a` - Run with coroutine workers

#### 4. Benchmarking

Run performance benchmarks against your agent:

```bash
aclip --env_path .env benchmark --payload_path ./payload.json --num_workers 10
```

Options:
- `--payload_path` / `-p` - Path to payload JSON file
- `--num_workers` / `-n` - Number of concurrent workers (default: `1`)
- `--verbose` / `-v` - Enable verbose logging
- `--async_mode` / `-a` - Use coroutine workers instead of threads

The benchmark command provides:
- Aggregated results with min/max/mean/median duration
- Success/failure rates
- Timeline visualization
- Throughput metrics

## Usage Examples

### Complete Integration Test Example

```python
import pytest
from microsoft_agents.testing import (
    Integration,
    AgentClient,
    ResponseClient,
    ddt,
)

@ddt("tests/my_agent/directline")
class TestMyAgentIntegration(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"

    @pytest.mark.asyncio
    async def test_custom_scenario(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        # Send activity
        await agent_client.send_activity("Hello")
        
        # Get responses
        responses = await response_client.pop()
        
        # Assert
        assert len(responses) > 0
        assert responses[0].text == "Hello! How can I help you?"
```

### Manual Agent Client Usage

```python
import asyncio
from microsoft_agents.testing import AgentClient
from microsoft_agents.activity import Activity

async def test_agent():
    client = AgentClient(
        agent_url="http://localhost:3978/",
        cid="conversation-id",
        client_id="your-client-id",
        tenant_id="your-tenant-id",
        client_secret="your-secret",
        service_url="http://localhost:8001/"
    )
    
    try:
        # Send expect-replies activity
        replies = await client.send_expect_replies(
            Activity(text="Hello", type="message")
        )
        
        for reply in replies:
            print(f"Reply: {reply.text}")
    
    finally:
        await client.close()

asyncio.run(test_agent())
```

### Custom Sample and Environment

```python
from microsoft_agents.testing import (
    Sample,
    Environment,
    AiohttpEnvironment,
)
from aiohttp import web

class MySample(Sample):
    async def init_app(self):
        # Initialize your application
        self.app = web.Application()
        # Configure routes, etc.
        return self.app
    
    @classmethod
    async def get_config(cls) -> dict:
        return {
            "CLIENT_ID": "your-client-id",
            "TENANT_ID": "your-tenant-id",
            "CLIENT_SECRET": "your-secret",
        }

# Use in tests
class TestMySample(Integration):
    _sample_cls = MySample
    _environment_cls = AiohttpEnvironment
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
```

### Utility Functions

```python
from microsoft_agents.testing import populate_activity, get_host_and_port
from microsoft_agents.activity import Activity

# Populate activity with defaults
defaults = Activity(channelId="directline", locale="en-US")
activity = Activity(type="message", text="Hello")
populated = populate_activity(activity, defaults)

# Parse URL
host, port = get_host_and_port("http://localhost:3978/")
# host = "localhost", port = 3978
```

## API Reference

### Classes

#### `Integration`
Base class for integration tests with pytest fixtures.

**Properties:**
- `service_url` - Service URL for responses
- `agent_url` - Agent URL for sending activities

**Fixtures:**
- `environment()` - Test environment instance
- `sample()` - Sample application instance
- `agent_client()` - Agent client for sending activities
- `response_client()` - Response client for receiving activities

**Methods:**
- `setup_method()` - Initialize test configuration
- `create_agent_client()` - Create agent client instance

#### `AgentClient`
Client for sending activities to an agent.

**Constructor Parameters:**
- `agent_url` - Agent endpoint URL
- `cid` - Conversation ID
- `client_id` - Azure AD client ID
- `tenant_id` - Azure AD tenant ID
- `client_secret` - Azure AD client secret
- `service_url` - Service URL for callbacks
- `default_activity_data` - Default activity values
- `default_sleep` - Default sleep duration after sending

**Methods:**
- `send_activity(activity_or_text, sleep)` - Send an activity
- `send_expect_replies(activity, sleep)` - Send and expect replies
- `send_invoke_activity(activity, sleep)` - Send invoke activity
- `close()` - Close the client session

#### `ResponseClient`
Mock service for receiving agent responses.

**Constructor Parameters:**
- `host` - Host address (default: `localhost`)
- `port` - Port number (default: `9873`)

**Methods:**
- `pop()` - Retrieve and clear received activities
- `__aenter__()` / `__aexit__()` - Async context manager support

#### `DataDrivenTest`
Runner for YAML-based data-driven tests.

**Constructor Parameters:**
- `test_flow` - Dictionary containing test configuration

**Properties:**
- `name` - Test name

**Methods:**
- `run(agent_client, response_client)` - Execute the test

#### `ModelAssertion`
Advanced assertion for model validation.

**Constructor Parameters:**
- `assertion` - Expected model or dict
- `selector` - Model selector for filtering
- `quantifier` - Assertion quantifier (ALL, ONE, NONE)

**Methods:**
- `check(items)` - Check items against assertion
- `from_config(config)` - Create from configuration dict

#### `ModelSelector`
Selector for filtering models.

**Constructor Parameters:**
- `model` - Model pattern to match
- `index` - Index to select

**Methods:**
- `select(items)` - Select matching items
- `select_first(items)` - Select first match

#### `SDKConfig`
Configuration loader for SDK settings.

**Constructor Parameters:**
- `env_path` - Path to .env file
- `load_into_environment` - Load into environment variables

**Properties:**
- `config` - Configuration dictionary (read-only copy)

**Methods:**
- `get_connection(connection_name)` - Get connection settings

### Functions

#### `generate_token(app_id, app_secret, tenant_id)`
Generate OAuth token for Azure Bot Service.

#### `generate_token_from_config(sdk_config)`
Generate token from SDK configuration.

#### `assert_field(actual_value, assertion, assertion_type)`
Assert a specific field value.

#### `assert_model(model, assertion)`
Assert an entire model matches expected structure.

#### `check_field(actual_value, assertion, assertion_type)`
Check field value without asserting.

#### `check_model(model, assertion)`
Check model without asserting.

#### `populate_activity(original, defaults)`
Populate activity with default values.

#### `get_host_and_port(url)`
Parse host and port from URL.

#### `ddt(path, prefix="")`
Decorator for data-driven test classes.

### Enums

#### `FieldAssertionType`
- `EQUALS` - Exact match
- `CONTAINS` - Contains value
- `EXISTS` - Field exists
- `NOT_EXISTS` - Field does not exist
- `GREATER_THAN` - Greater than value
- `LESS_THAN` - Less than value

#### `AssertionQuantifier`
- `ALL` - All items must match
- `ONE` - Exactly one item must match
- `NONE` - No items should match

## Future Goals

The following features and improvements are planned to enhance the usability and power of the microsoft-agents-testing package:

### 1. Enhanced Test Recording and Playback
- **Interactive Test Recorder**: Capture live agent interactions and automatically generate YAML test definitions
- **Conversation Replay**: Record entire conversations and replay them for regression testing
- **Smart Diff Tools**: Detect changes between recorded and actual responses with intelligent comparison

### 2. Advanced Mocking Capabilities
- **External Service Mocking**: Built-in support for mocking external APIs and services that agents depend on
- **Channel Simulators**: More realistic channel-specific behavior simulation (Teams, Slack, etc.)
- **Network Condition Simulation**: Test agents under various network conditions (latency, packet loss)

### 3. Improved Assertion Framework
- **Visual Assertions**: Assert on rich content like Adaptive Cards with visual diff tools
- **Fuzzy Matching**: Support for approximate string matching and similarity scores
- **Custom Assertion Plugins**: Allow users to define custom assertion types
- **Assertion Templates**: Pre-built assertion patterns for common scenarios

### 4. Performance and Scalability
- **Distributed Load Testing**: Run benchmarks across multiple machines
- **Real-time Metrics Dashboard**: Live visualization of benchmark results
- **Memory Profiling**: Built-in memory usage tracking during tests
- **Async/Await Optimization**: Better support for free-threaded Python and async workloads

### 5. Better Developer Experience
- **VS Code Extension**: Integrated test runner and YAML editor with IntelliSense
- **Test Generation Wizard**: Interactive CLI tool to scaffold new test suites
- **Enhanced Error Messages**: More detailed and actionable error messages with suggested fixes
- **Auto-completion**: Schema-based auto-completion for YAML test files

### 6. CI/CD Integration
- **Test Report Formats**: Support for JUnit XML, TAP, and other standard formats
- **GitHub Actions Integration**: Pre-built actions for running agent tests
- **Azure DevOps Tasks**: Custom pipeline tasks for Azure Pipelines
- **Test Result Analytics**: Track test performance over time with trend analysis

### 7. Multi-Agent Testing
- **Agent-to-Agent Testing**: Test communication between multiple agents
- **Orchestration Testing**: Test complex multi-agent workflows
- **State Management**: Better support for testing stateful conversations across agents

### 8. Security Testing
- **Authentication Flow Testing**: Comprehensive OAuth and SSO flow validation
- **Permission Testing**: Verify proper authorization checks
- **Security Scan Integration**: Integrate with security scanning tools
- **PII Detection**: Automatically detect and flag potential PII leaks

### 9. Documentation and Learning
- **Interactive Tutorial**: Step-by-step guide with executable examples
- **Best Practices Guide**: Comprehensive testing patterns and anti-patterns
- **Video Tutorials**: Video content for common testing scenarios
- **Sample Test Repository**: Curated collection of example tests

### 10. Advanced DDT Features
- **Parameterized Tests**: Support for test parameters and matrix testing
- **Conditional Execution**: Execute test steps based on conditions
- **Dynamic Test Generation**: Generate tests programmatically from schemas
- **Test Composition**: Compose larger tests from reusable test fragments

### 11. Telemetry and Observability
- **OpenTelemetry Integration**: Export test traces to observability platforms
- **Test Coverage Metrics**: Track which agent capabilities are tested
- **Flaky Test Detection**: Identify and mark unstable tests
- **Performance Regression Detection**: Automatically detect performance degradation

### 12. Cross-Platform Support
- **Browser-based Testing**: Test web-based bot interfaces
- **Mobile Emulation**: Test agents in mobile contexts
- **Multi-Language Support**: Better support for testing agents in different languages and locales

## Contributing

Contributions are welcome! This is an experimental development package designed to improve testing workflows for Microsoft Agents.

### Development Setup

1. Clone the repository
2. Install in editable mode:
   ```bash
   pip install -e ./microsoft-agents-testing/ --config-settings editable_mode=compat
   ```
3. Run tests:
   ```bash
   pytest tests/
   ```

### Guidelines

- Follow existing code style and patterns
- Add tests for new features
- Update documentation for API changes
- Use type hints for better IDE support

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/microsoft/Agents).

---

**Note**: This package is part of the Microsoft Agents SDK development tools and is intended for testing and development purposes. For production agent hosting, use the core Microsoft Agents packages.

# Microsoft 365 Agents SDK for Python - Testing Framework

A comprehensive testing framework designed specifically for Microsoft 365 Agents SDK, providing essential utilities and abstractions to streamline integration testing, authentication, data-driven testing, and end-to-end agent validation.

## Table of Contents

- [Why This Package Exists](#why-this-package-exists)
- [Key Features](#key-features)
  - [Authentication Utilities](#authentication-utilities)
  - [Integration Test Framework](#integration-test-framework)
  - [Agent Communication Clients](#agent-communication-clients)
  - [Data-Driven Testing](#data-driven-testing)
  - [Advanced Assertions Framework](#advanced-assertions-framework)
  - [Testing Utilities](#testing-utilities)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Advanced Examples](#advanced-examples)
- [API Reference](#api-reference)
- [CI/CD Integration](#cicd-integration)
- [Contributing](#contributing)

## Why This Package Exists

Building and testing conversational agents presents unique challenges that standard testing frameworks don't address. This package eliminates these pain points by providing powerful abstractions specifically designed for agent testing scenarios, including support for data-driven testing with YAML/JSON configurations.

**Key Benefits:**
- Write tests once in YAML/JSON, run them everywhere
- Reduce boilerplate code with pre-built fixtures and clients
- Validate complex conversation flows with declarative assertions
- Maintain test suites that are easy to read and maintain
- Integrate seamlessly with pytest and CI/CD pipelines

## Key Features

### 🔐 Authentication Utilities

Generate OAuth2 access tokens for testing secured agents with Microsoft Authentication Library (MSAL) integration.

**Features:**
- Client credentials flow support
- Environment variable configuration
- SDK config integration

**Example:**

```python
from microsoft_agents.testing import generate_token, generate_token_from_config

# Generate token directly
token = generate_token(
    app_id="your-app-id",
    app_secret="your-secret",
    tenant_id="your-tenant"
)

# Or from SDK config
token = generate_token_from_config(sdk_config)
```

### 🧪 Integration Test Framework

Pre-built pytest fixtures and abstractions for agent integration testing.

**Features:**
- Pytest fixture integration
- Environment abstraction for different hosting configurations
- Sample management for test organization
- Application lifecycle management
- Automatic setup and teardown

**Example:**

```python
from microsoft_agents.testing import Integration, AiohttpEnvironment, Sample

class MyAgentSample(Sample):
    async def init_app(self):
        self.app = create_my_agent_app(self.env)
    
    @classmethod
    async def get_config(cls):
        return {"service_url": "http://localhost:3978"}

class MyAgentTests(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, agent_client, sample):
        # Client and sample are automatically set up via fixtures
        response = await agent_client.send_activity("Hello")
        assert response is not None
```

### 🤖 Agent Communication Clients

High-level clients for sending and receiving activities from agents under test.

**Features:**
- Simple text message sending
- Full Activity object support
- Automatic token management
- Support for `expectReplies` delivery mode
- Response collection and management

**AgentClient Example:**

```python
from microsoft_agents.testing import AgentClient
from microsoft_agents.activity import Activity, ActivityTypes

client = AgentClient(
    agent_url="http://localhost:3978",
    cid="conversation-id",
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    client_secret="your-secret"
)

# Send simple text message
response = await client.send_activity("What's the weather?")

# Send full Activity object
activity = Activity(type=ActivityTypes.message, text="Hello")
response = await client.send_activity(activity)

# Send with expectReplies delivery mode
replies = await client.send_expect_replies("What can you do?")
for reply in replies:
    print(reply.text)
```

**ResponseClient Example:**

```python
from microsoft_agents.testing import ResponseClient

# Create response client to collect agent responses
async with ResponseClient(host="localhost", port=9873) as response_client:
    # ... send activities with agent_client ...
    
    # Collect all responses
    responses = await response_client.pop()
    assert len(responses) > 0
```

### 📋 Data-Driven Testing

Write test scenarios in YAML or JSON files and execute them automatically. Perfect for creating reusable test suites, regression tests, and living documentation.

**Features:**
- Declarative test definition in YAML/JSON
- Parent/child file inheritance for shared defaults
- Multiple step types (input, assertion, sleep, breakpoint)
- Flexible assertions with selectors and quantifiers
- Automatic test discovery and generation
- Field-level assertion operators

#### Using the @ddt Decorator

The @ddt (data-driven tests) decorator automatically loads test files and generates pytest test methods:

```python
from microsoft_agents.testing import Integration, AiohttpEnvironment, ddt

@ddt("tests/my_agent/test_cases", recursive=True)
class TestMyAgent(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    _agent_url = "http://localhost:3978"
    _cid = "test-conversation"
```

This will:
1. Load all `.yaml` and `.json` files from `tests/my_agent/test_cases` (and subdirectories if `recursive=True`)
2. Create a pytest test method for each file (e.g., `test_data_driven__greeting_test`)
3. Execute the test flow defined in each file

#### Test File Format

**Shared Defaults (parent.yaml):**

```yaml
name: directline
defaults:
  input:
    activity:
      channelId: directline
      locale: en-US
      serviceUrl: http://localhost:56150
      deliveryMode: expectReplies
      conversation:
        id: conv1
      from:
        id: user1
        name: User
      recipient:
        id: bot
        name: Bot
```

**Test File (greeting_test.yaml):**

```yaml
parent: parent.yaml
name: greeting_test
description: Test basic greeting conversation
test:
  - type: input
    activity:
      type: message
      text: hello world
  
  - type: assertion
    selector:
      activity:
        type: message
    activity:
      type: message
      text: "[0] You said: hello world"
  
  - type: input
    activity:
      type: message
      text: hello again
  
  - type: assertion
    selector:
      index: -1  # Select the last matching activity
      activity:
        type: message
    activity:
      type: message
      text: "[1] You said: hello again"
```

#### Test Step Types

##### Input Steps

Send activities to the agent under test:

```yaml
- type: input
  activity:
    type: message
    text: "What's the weather?"
```

With overrides:

```yaml
- type: input
  activity:
    type: message
    text: "Hello"
    locale: "fr-FR"  # Override default locale
    channelData:
      custom: "value"
```

##### Assertion Steps

Verify agent responses with flexible matching:

```yaml
- type: assertion
  quantifier: all  # Options: all, any, one, none
  selector:
    index: 0  # Optional: select by index (0, -1, etc.)
    activity:
      type: message  # Filter by activity fields
  activity:
    type: message
    text: ["CONTAINS", "sunny"]  # Use operators for flexible matching
```

**Quantifiers:**
- `all` (default): Every selected activity must match
- `any`: At least one activity must match
- `one`: Exactly one activity must match
- `none`: No activities should match

**Selectors:**
- `activity`: Filter activities by field values
- `index`: Select specific activity by index (supports negative indices)

**Field Assertion Operators:**
- `["CONTAINS", "substring"]`: Check if string contains substring
- `["NOT_CONTAINS", "substring"]`: Check if string doesn't contain substring
- `["RE_MATCH", "pattern"]`: Check if string matches regex pattern
- `["IN", [list]]`: Check if value is in list
- `["NOT_IN", [list]]`: Check if value is not in list
- `["EQUALS", value]`: Explicit equality check
- `["NOT_EQUALS", value]`: Explicit inequality check
- `["GREATER_THAN", number]`: Numeric comparison
- `["LESS_THAN", number]`: Numeric comparison
- Direct value: Implicit equality check

##### Sleep Steps

Add delays between operations:

```yaml
- type: sleep
  duration: 0.5  # seconds
```

With default duration:

```yaml
defaults:
  sleep:
    duration: 0.2

test:
  - type: sleep  # Uses default duration
```

##### Breakpoint Steps

Pause execution for debugging:

```yaml
- type: breakpoint
```

When the test reaches this step, it will trigger a Python breakpoint, allowing you to inspect state in a debugger.

#### Loading Tests Programmatically

Load and run tests manually without the decorator:

```python
from microsoft_agents.testing import load_ddts, DataDrivenTest

# Load all test files from a directory
tests = load_ddts("tests/my_agent", recursive=True)

# Run specific tests
for test in tests:
    print(f"Running: {test.name}")
    await test.run(agent_client, response_client)
```

Load from specific file:

```python
tests = load_ddts("tests/greeting_test.yaml", recursive=False)
test = tests[0]
await test.run(agent_client, response_client)
```

### ✅ Advanced Assertions Framework

Powerful assertion system for validating agent responses with flexible matching criteria.

#### ModelAssertion

Create assertions for validating lists of activities:

```python
from microsoft_agents.testing import ModelAssertion, Selector, AssertionQuantifier

# Create an assertion
assertion = ModelAssertion(
    assertion={"type": "message", "text": "Hello"},
    selector=Selector(selector={"type": "message"}),
    quantifier=AssertionQuantifier.ALL
)

# Test activities
activities = [...]  # List of Activity objects
passes, error = assertion.check(activities)

# Or use as callable (raises AssertionError on failure)
assertion(activities)
```

From configuration dictionary:

```python
config = {
    "activity": {"type": "message", "text": "Hello"},
    "selector": {"activity": {"type": "message"}},
    "quantifier": "all"
}
assertion = ModelAssertion.from_config(config)
```

#### Selectors

Filter activities before validation:

```python
from microsoft_agents.testing import Selector

# Select all message activities
selector = Selector(selector={"type": "message"})
messages = selector(activities)

# Select the first message activity
selector = Selector(selector={"type": "message"}, index=0)
first_message = selector.select_first(activities)

# Select the last message activity
selector = Selector(selector={"type": "message"}, index=-1)
last_message = selector(activities)[0]

# Select by multiple fields
selector = Selector(selector={
    "type": "message",
    "locale": "en-US",
    "channelId": "directline"
})
```

From configuration:

```python
config = {
    "activity": {"type": "message"},
    "index": -1
}
selector = Selector.from_config(config)
```

#### Quantifiers

Control how many activities must match the assertion:

```python
from microsoft_agents.testing import AssertionQuantifier

# ALL: Every selected activity must match (default)
quantifier = AssertionQuantifier.ALL

# ANY: At least one activity must match
quantifier = AssertionQuantifier.ANY

# ONE: Exactly one activity must match
quantifier = AssertionQuantifier.ONE

# NONE: No activities should match
quantifier = AssertionQuantifier.NONE

# From string
quantifier = AssertionQuantifier.from_config("all")
```

#### Field Assertions

Test individual fields with operators:

```python
from microsoft_agents.testing import check_field, FieldAssertionType

# String contains
result = check_field("Hello world", ["CONTAINS", "world"])  # True

# Regex match
result = check_field("ID-12345", ["RE_MATCH", r"ID-\d+"])  # True

# Value in list
result = check_field(5, ["IN", [1, 3, 5, 7]])  # True

# Value not in list
result = check_field(2, ["NOT_IN", [1, 3, 5, 7]])  # True

# Numeric comparisons
result = check_field(10, ["GREATER_THAN", 5])  # True
result = check_field(3, ["LESS_THAN", 10])  # True

# String doesn't contain
result = check_field("Hello", ["NOT_CONTAINS", "world"])  # True

# Exact equality
result = check_field("test", "test")  # True
result = check_field(42, ["EQUALS", 42])  # True

# Inequality
result = check_field("foo", ["NOT_EQUALS", "bar"])  # True
```

Verbose checking with error details:

```python
from microsoft_agents.testing import check_field_verbose

passes, error_data = check_field_verbose("Hello", ["CONTAINS", "world"])
if not passes:
    print(f"Field: {error_data.field_path}")
    print(f"Actual: {error_data.actual_value}")
    print(f"Expected: {error_data.assertion}")
    print(f"Type: {error_data.assertion_type}")
```

#### Activity Assertions

Check entire activities:

```python
from microsoft_agents.testing import check_model, assert_model

activity = Activity(type="message", text="Hello", locale="en-US")

# Check without raising exception
assertion = {"type": "message", "text": ["CONTAINS", "Hello"]}
result = check_activity(activity, assertion)  # True

# Check with detailed error information
passes, error_data = check_activity_verbose(activity, assertion)

# Assert with exception on failure
assert_model(activity, assertion)  # Raises AssertionError if fails
```

Nested field checking:

```python
assertion = {
    "type": "message",
    "channelData": {
        "user": {
            "id": ["RE_MATCH", r"user-\d+"]
        }
    }
}
assert_model(activity, assertion)
```

### 🛠️ Testing Utilities

Helper functions for common testing operations.

#### populate_activity

Fill activity objects with default values:

```python
from microsoft_agents.testing import populate_activity
from microsoft_agents.activity import Activity

defaults = {
    "service_url": "http://localhost",
    "channel_id": "test",
    "locale": "en-US"
}

activity = Activity(type="message", text="Hello")
activity = populate_activity(activity, defaults)

# activity now has service_url, channel_id, and locale set
```

#### get_host_and_port

Parse URLs to extract host and port:

```python
from microsoft_agents.testing import get_host_and_port

host, port = get_host_and_port("http://localhost:3978/api/messages")
# Returns: ("localhost", 3978)

host, port = get_host_and_port("https://myagent.azurewebsites.net")
# Returns: ("myagent.azurewebsites.net", 443)
```

## Installation

```bash
pip install microsoft-agents-testing
```

For development:

```bash
pip install microsoft-agents-testing[dev]
```

## Quick Start

### Traditional Integration Testing

```python
import pytest
from microsoft_agents.testing import Integration, AiohttpEnvironment, Sample
from microsoft_agents.activity import Activity

class MyAgentSample(Sample):
    async def init_app(self):
        # Initialize your agent application
        from my_agent import create_app
        self.app = create_app(self.env)
    
    @classmethod
    async def get_config(cls):
        return {
            "service_url": "http://localhost:3978",
            "app_id": "test-app-id",
        }

class TestMyAgent(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    
    _agent_url = "http://localhost:3978"
    _cid = "test-conversation"
    
    @pytest.mark.asyncio
    async def test_greeting(self, agent_client):
        response = await agent_client.send_activity("Hello")
        assert "Hi there" in response
    
    @pytest.mark.asyncio
    async def test_conversation(self, agent_client):
        replies = await agent_client.send_expect_replies("What can you do?")
        assert len(replies) > 0
        assert replies[0].type == "message"
```

### Data-Driven Testing

**Step 1:** Create test YAML files in `tests` directory

```yaml
# tests/greeting.yaml
name: greeting_test
description: Test basic greeting functionality
defaults:
  input:
    activity:
      type: message
      locale: en-US
      channelId: directline
test:
  - type: input
    activity:
      text: Hello
  
  - type: assertion
    activity:
      type: message
      text: ["CONTAINS", "Hi"]
```

**Step 2:** Add the @ddt decorator to your test class

```python
from microsoft_agents.testing import Integration, AiohttpEnvironment, ddt

@ddt("tests", recursive=True)
class TestMyAgent(Integration):
    _sample_cls = MyAgentSample
    _environment_cls = AiohttpEnvironment
    _agent_url = "http://localhost:3978"
```

**Step 3:** Run tests with pytest

```bash
pytest tests/ -v
```

Output:
```
tests/test_my_agent.py::TestMyAgent::test_data_driven__greeting_test PASSED
```

## Usage Guide

### Setting Up Authentication

#### From Environment Variables

```python
import os
from microsoft_agents.testing import generate_token

token = generate_token(
    app_id=os.getenv("CLIENT_ID"),
    app_secret=os.getenv("CLIENT_SECRET"),
    tenant_id=os.getenv("TENANT_ID")
)
```

#### From SDK Config

```python
from microsoft_agents.testing import SDKConfig, generate_token_from_config

config = SDKConfig()
# config loads from environment or config file
token = generate_token_from_config(config)
```

### Creating Custom Environments

```python
from microsoft_agents.testing import Environment
from aiohttp import web

class MyCustomEnvironment(Environment):
    async def init_env(self, config: dict):
        # Custom initialization
        self.config = config
        # Set up any required services, databases, etc.
    
    def create_runner(self, host: str, port: int):
        # Return application runner
        from my_agent import create_app
        app = create_app(self)
        return MyAppRunner(app, host, port)
```

### Writing Complex Assertions

```yaml
test:
  - type: input
    activity:
      type: message
      text: "Get user profile for user123"
  
  - type: assertion
    quantifier: one
    selector:
      activity:
        type: message
    activity:
      type: message
      text: ["RE_MATCH", ".*user123.*"]
      attachments:
        - contentType: "application/vnd.microsoft.card.adaptive"
      channelData:
        userId: "user123"
```

## Advanced Examples

### Complex Weather Conversation

```yaml
name: weather_conversation
description: Test multi-turn weather conversation flow
defaults:
  input:
    activity:
      type: message
      channelId: directline
      locale: en-US
      conversation:
        id: weather-conv-1
  assertion:
    quantifier: all
test:
  # Initial weather query
  - type: input
    activity:
      text: "What's the weather in Seattle?"
  
  - type: assertion
    selector:
      activity:
        type: message
    activity:
      type: message
      text: ["CONTAINS", "Seattle"]
  
  # Wait for async processing
  - type: sleep
    duration: 0.2
  
  # Follow-up question
  - type: input
    activity:
      text: "What about tomorrow?"
  
  - type: assertion
    selector:
      activity:
        type: message
    activity:
      type: message
      text: ["RE_MATCH", "tomorrow.*forecast"]
  
  # Verify we got exactly one final response
  - type: assertion
    quantifier: one
    selector:
      index: -1
      activity:
        type: message
    activity:
      type: message
```

### Testing Invoke Activities

```yaml
parent: parent.yaml
name: test_invoke_profile
test:
  - type: input
    activity:
      type: invoke
      name: getUserProfile
      value:
        userId: "12345"
  
  # Ensure we don't get error responses
  - type: assertion
    quantifier: none
    activity:
      type: invokeResponse
      value:
        status: ["IN", [400, 404, 500]]
  
  # Verify successful response
  - type: assertion
    selector:
      activity:
        type: invokeResponse
    activity:
      type: invokeResponse
      value:
        status: 200
        body:
          userId: "12345"
          name: ["CONTAINS", "John"]
          email: ["RE_MATCH", ".*@example\\.com"]
```

### Testing Conversation Update

```yaml
parent: parent.yaml
name: conversation_update_test
test:
  - type: input
    activity:
      type: conversationUpdate
      membersAdded:
        - id: bot-id
          name: bot
        - id: user
      from:
        id: user
      recipient:
        id: bot-id
        name: bot
      channelData:
        clientActivityId: "123"
  
  - type: assertion
    selector:
      activity:
        type: message
    activity:
      type: message
      text: ["CONTAINS", "Hello and Welcome!"]
```

### Conditional Responses

```yaml
test:
  - type: input
    activity:
      text: "Show me options"
  
  # Verify at least one message was sent
  - type: assertion
    quantifier: any
    selector:
      activity:
        type: message
    activity:
      type: message
  
  # Verify adaptive card was included
  - type: assertion
    quantifier: one
    selector:
      activity:
        attachments:
          - contentType: "application/vnd.microsoft.card.adaptive"
    activity:
      type: message
```

### Testing with Message Reactions

```yaml
parent: parent.yaml
test:
  # Send initial message
  - type: input
    activity:
      type: message
      text: "Great job!"
      id: "msg-123"
  
  # Add a reaction
  - type: input
    activity:
      type: messageReaction
      reactionsAdded:
        - type: like
      replyToId: "msg-123"
  
  - type: assertion
    selector:
      activity:
        type: message
    activity:
      type: message
      text: ["CONTAINS", "Thanks for the reaction"]
```

## API Reference

### Classes

#### Integration
Base class for integration tests with pytest fixtures.

```python
class Integration:
    _sample_cls: type[Sample]
    _environment_cls: type[Environment]
    _agent_url: str
    _service_url: str
    _cid: str
    _client_id: str
    _tenant_id: str
    _client_secret: str
    
    @pytest.fixture
    async def environment(self) -> Environment: ...
    
    @pytest.fixture
    async def sample(self, environment) -> Sample: ...
    
    @pytest.fixture
    async def agent_client(self, sample, environment) -> AgentClient: ...
    
    @pytest.fixture
    async def response_client(self) -> ResponseClient: ...
```

#### AgentClient
Client for sending activities to agents.

```python
class AgentClient:
    def __init__(
        self,
        agent_url: str,
        cid: str,
        client_id: str,
        tenant_id: str,
        client_secret: str,
        service_url: Optional[str] = None,
        default_timeout: float = 5.0,
        default_activity_data: Optional[Activity | dict] = None
    ): ...
    
    async def send_activity(
        self,
        activity_or_text: Activity | str,
        sleep: float = 0,
        timeout: Optional[float] = None
    ) -> str: ...
    
    async def send_expect_replies(
        self,
        activity_or_text: Activity | str,
        sleep: float = 0,
        timeout: Optional[float] = None
    ) -> list[Activity]: ...
    
    async def close(self) -> None: ...
```

#### ResponseClient
Client for receiving activities from agents.

```python
class ResponseClient:
    def __init__(self, host: str = "localhost", port: int = 9873): ...
    
    async def pop(self) -> list[Activity]: ...
    
    async def __aenter__(self) -> ResponseClient: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

#### DataDrivenTest
Runner for YAML/JSON test definitions.

```python
class DataDrivenTest:
    def __init__(self, test_flow: dict) -> None: ...
    
    @property
    def name(self) -> str: ...
    
    async def run(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ) -> None: ...
```

#### ModelAssertion
Assertion engine for validating activities.

```python
class ModelAssertion:
    def __init__(
        self,
        assertion: dict | Activity | None = None,
        selector: Selector | None = None,
        quantifier: AssertionQuantifier = AssertionQuantifier.ALL
    ): ...
    
    def check(self, activities: list[Activity]) -> tuple[bool, Optional[str]]: ...
    
    def __call__(self, activities: list[Activity]) -> None: ...
    
    @staticmethod
    def from_config(config: dict) -> ModelAssertion: ...
```

#### Selector
Filter activities based on criteria.

```python
class Selector:
    def __init__(
        self,
        selector: dict | Activity | None = None,
        index: int | None = None
    ): ...
    
    def select(self, activities: list[Activity]) -> list[Activity]: ...
    
    def select_first(self, activities: list[Activity]) -> Activity | None: ...
    
    def __call__(self, activities: list[Activity]) -> list[Activity]: ...
    
    @staticmethod
    def from_config(config: dict) -> Selector: ...
```

#### AssertionQuantifier
Quantifiers for assertions.

```python
class AssertionQuantifier(str, Enum):
    ALL = "ALL"
    ANY = "ANY"
    ONE = "ONE"
    NONE = "NONE"
    
    @staticmethod
    def from_config(value: str) -> AssertionQuantifier: ...
```

#### FieldAssertionType
Types of field assertions.

```python
class FieldAssertionType(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    RE_MATCH = "RE_MATCH"
```

### Decorators

#### @ddt
Load and execute data-driven tests.

```python
def ddt(test_path: str, recursive: bool = True) -> Callable:
    """
    Decorator to add data-driven tests to an integration test class.
    
    :param test_path: Path to test files directory
    :param recursive: Load tests from subdirectories
    """
```

### Functions

#### generate_token
Generate OAuth2 access token.

```python
def generate_token(app_id: str, app_secret: str, tenant_id: str) -> str: ...
```

#### generate_token_from_config
Generate token from SDK config.

```python
def generate_token_from_config(sdk_config: SDKConfig) -> str: ...
```

#### load_ddts
Load data-driven test files.

```python
def load_ddts(
    path: str | Path | None = None,
    recursive: bool = False
) -> list[DataDrivenTest]: ...
```

#### populate_activity
Fill activity with default values.

```python
def populate_activity(
    activity: Activity,
    defaults: dict | Activity
) -> Activity: ...
```

#### get_host_and_port
Parse host and port from URL.

```python
def get_host_and_port(url: str) -> tuple[str, int]: ...
```

#### check_activity
Check if activity matches assertion.

```python
def check_activity(activity: Activity, assertion: dict | Activity) -> bool: ...
```

#### check_activity_verbose
Check activity with detailed error information.

```python
def check_activity_verbose(
    activity: Activity,
    assertion: dict | Activity
) -> tuple[bool, Optional[AssertionErrorData]]: ...
```

#### check_field
Check if field value matches assertion.

```python
def check_field(value: Any, assertion: Any) -> bool: ...
```

#### check_field_verbose
Check field with detailed error information.

```python
def check_field_verbose(
    value: Any,
    assertion: Any,
    field_path: str = ""
) -> tuple[bool, Optional[AssertionErrorData]]: ...
```

#### assert_model
Assert activity matches, raise on failure.

```python
def assert_model(activity: Activity, assertion: dict | Activity) -> None: ...
```

#### assert_field
Assert field matches, raise on failure.

```python
def assert_field(value: Any, assertion: Any, field_path: str = "") -> None: ...
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install microsoft-agents-testing pytest pytest-asyncio
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        CLIENT_ID: ${{ secrets.AGENT_CLIENT_ID }}
        CLIENT_SECRET: ${{ secrets.AGENT_CLIENT_SECRET }}
        TENANT_ID: ${{ secrets.TENANT_ID }}
    
    - name: Run data-driven tests
      run: pytest tests/data_driven/ -v
```

### Azure DevOps

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install -r requirements.txt
    pip install microsoft-agents-testing pytest pytest-asyncio
  displayName: 'Install dependencies'

- script: |
    pytest tests/ -v --junitxml=test-results.xml
  displayName: 'Run tests'
  env:
    CLIENT_ID: $(CLIENT_ID)
    CLIENT_SECRET: $(CLIENT_SECRET)
    TENANT_ID: $(TENANT_ID)

- task: PublishTestResults@2
  inputs:
    testResultsFiles: 'test-results.xml'
    testRunTitle: 'Agent Integration Tests'
```

## Who Should Use This Package

- **Agent Developers**: Testing agents built with `microsoft-agents-hosting-core` and related packages
- **QA Engineers**: Writing integration, E2E, and regression tests for conversational AI systems
- **DevOps Teams**: Automating agent validation in CI/CD pipelines
- **Sample Authors**: Creating reproducible examples and living documentation
- **Test Engineers**: Building comprehensive test suites with data-driven testing
- **Product Managers**: Writing human-readable test specifications in YAML

## Related Packages

This package complements the Microsoft 365 Agents SDK ecosystem:

- **`microsoft-agents-activity`**: Activity types and protocols
- **`microsoft-agents-hosting-core`**: Core hosting framework
- **`microsoft-agents-hosting-aiohttp`**: aiohttp hosting integration
- **`microsoft-agents-hosting-fastapi`**: FastAPI hosting integration
- **`microsoft-agents-hosting-teams`**: Teams-specific hosting features
- **`microsoft-agents-authentication-msal`**: MSAL authentication
- **`microsoft-agents-storage-blob`**: Azure Blob storage for agent state
- **`microsoft-agents-storage-cosmos`**: Azure Cosmos DB storage for agent state

## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit [https://cla.opensource.microsoft.com](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## License

MIT License

Copyright (c) Microsoft Corporation.

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [https://github.com/microsoft/Agents-for-python/issues](https://github.com/microsoft/Agents-for-python/issues)
- **Documentation**: [https://github.com/microsoft/Agents-for-python](https://github.com/microsoft/Agents-for-python)
- **Stack Overflow**: Tag your questions with `microsoft-agents-sdk`

## Changelog

See CHANGELOG.md for version history and release notes.

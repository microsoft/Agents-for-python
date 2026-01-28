# Microsoft Agents Testing Framework

A powerful, developer-friendly testing framework for agents built with the M365 Agents SDK for Python. Write expressive, maintainable tests with minimal boilerplate—so you can focus on building great agents.

## Why This Framework?

Testing conversational agents is hard. You need to:
- Send messages and handle async responses
- Filter through multiple activity types
- Make assertions on complex nested data
- Simulate multi-turn conversations
- Track full conversation transcripts
- Verify internal agent state during execution

This framework handles all of that with an elegant, chainable API that makes your tests read like natural language.

## Installation

```bash
pip install microsoft-agents-testing
```

## Quick Start

```python
import pytest
from microsoft_agents.testing import Check

# Point to your running agent
@pytest.mark.agent_test("http://localhost:3978/api/messages")
class TestMyAgent:

    @pytest.mark.asyncio
    async def test_agent_says_hello(self, conv):
        # Send a message and get responses
        responses = await conv.say("Hello!")
        
        # Assert the agent replied with a greeting
        Check(responses).where(type="message").that(
            text=lambda x: "Hello" in x or "Hi" in x
        )
```

That's it. No HTTP setup, no callback servers, no activity parsing. Just send messages and make assertions.

---

## Core Components

### 🎯 `Check` — Fluent Assertions for Any Data

The `Check` class provides a powerful, chainable API for filtering and asserting on agent responses.

#### Simple Assertions

```python
# Assert there's at least one message
Check(responses).where(type="message").is_not_empty()

# Assert the last message contains expected text
Check(responses).where(type="message").last().that(text="pong")

# Assert all messages match a condition
Check(responses).where(type="message").that_for_all(
    text=lambda x: len(x) > 0  # All messages have text
)
```

#### Complex Filtering

```python
# Chain filters for precise selection
messages = Check(responses) \
    .where(type="message") \
    .where_not(text="") \
    .order_by("timestamp")

# Get the first high-priority item
Check(items).where(priority=lambda p: p > 5).first().that(status="urgent")

# Assert exactly one item matches
Check(responses).that_for_one(type="typing")
```

#### Lambda Parameters

Lambdas in `Check` assertions support special parameters for powerful data access:

| Parameter | Description |
|-----------|-------------|
| `x`, `actual` | The current property value being checked |
| `root` | The root object (entire response/item) |
| `parent` | The parent object of the current property |

```python
# Simple: check the text property value
Check(responses).where(type="message").that(
    text=lambda x: "confirmed" in x.lower()
)

# Access root: validate text based on another field
Check(responses).where(type="message").that(
    text=lambda actual, root: root.locale == "es-ES" or "Hello" in actual
)

# Access parent: check nested data relative to its container
Check(responses).that(
    **{"data.status": lambda x, parent: x == "complete" and parent.get("id") is not None}
)

# Combine all: complex cross-field validation
Check(orders).that(
    **{"items.0.price": lambda actual, root, parent: (
        actual > 0 and 
        parent.get("quantity", 0) > 0 and
        root.status == "confirmed"
    )}
)
```

#### Quantifier Assertions

```python
# Assert conditions across multiple items
Check(responses).that_for_all(type="message")      # All are messages
Check(responses).that_for_any(text="error")        # At least one has error
Check(responses).that_for_none(status="failed")    # None have failed status
Check(responses).that_for_exactly(2, type="card")  # Exactly 2 cards
```

---

### 💬 `ConversationClient` — Natural Conversation Flow

High-level client that makes multi-turn conversations feel natural.

```python
@pytest.mark.asyncio
async def test_booking_flow(self, conv):
    # Simulate a real conversation
    await conv.say("I want to book a flight")
    await conv.say("New York to London")
    await conv.say("Next Friday")
    
    responses = await conv.say("Confirm booking")
    
    Check(responses).where(type="message").that(
        text=lambda x: "confirmed" in x.lower()
    )
```

#### Waiting for Async Responses

Use `wait_for` and `expect` to handle agents that respond asynchronously:

```python
@pytest.mark.asyncio
async def test_async_processing(self, conv):
    conv.timeout = 10.0  # Set timeout for waiting
    
    # Send a message that triggers background processing
    await conv.say("Process my order")
    
    # Wait for a specific response (returns when matched or times out)
    responses = await conv.wait_for(type="message", text=lambda x: "complete" in x)
    
    Check(responses).where(type="message").is_not_empty()
```

```python
@pytest.mark.asyncio
async def test_expect_typing_indicator(self, conv):
    conv.timeout = 5.0
    
    await conv.say("Tell me a long story")
    
    # Expect will raise AssertionError if condition not met within timeout
    await conv.expect(type="typing")
    
    # Continue waiting for the actual response
    responses = await conv.wait_for(type="message")
    Check(responses).where(type="message").that(
        text=lambda x: len(x) > 100  # It's a long story!
    )
```

```python
@pytest.mark.asyncio
async def test_wait_for_card_response(self, conv):
    conv.timeout = 8.0
    
    await conv.say("Show me the dashboard")
    
    # Wait for a message with an adaptive card attachment
    responses = await conv.wait_for(
        type="message",
        attachments=lambda a: len(a) > 0
    )
    
    Check(responses).where(type="message").that(
        attachments=lambda x, root: (
            any(att.content_type == "application/vnd.microsoft.card.adaptive" for att in x)
        )
    )
```

---

### 📡 `AgentClient` — Full Control When You Need It

When you need lower-level access to activities and exchanges:

```python
@pytest.mark.asyncio
async def test_with_full_control(self, agent_client):
    from microsoft_agents.activity import Activity, ActivityTypes
    
    # Send a custom activity
    activity = Activity(
        type=ActivityTypes.message,
        text="Hello",
        locale="es-ES"
    )
    
    # Get responses as exchanges (includes metadata)
    exchanges = await agent_client.ex_send(activity)
    
    # Each exchange contains request, responses, status, timing info
    exchange = exchanges[0]
    print(f"Status: {exchange.status_code}")
    print(f"Responses: {len(exchange.responses)}")
```

---

### 📜 `Transcript` — Complete Conversation History

Track every exchange in a conversation for debugging or analysis.

```python
@pytest.mark.asyncio
async def test_conversation_transcript(self, agent_client):
    await agent_client.send("Hello")
    await agent_client.send("How are you?")
    await agent_client.send("Goodbye")
    
    # Get complete transcript
    transcript = agent_client.transcript
    
    # Print all messages using the built-in helper
    from microsoft_agents.testing import print_messages
    print_messages(transcript)
```

The `print_messages` function provides a clean view of the conversation:

```python
# Here's what print_messages does under the hood:
def print_messages(transcript):
    for exchange in transcript.get_all():
        if exchange.request is not None and exchange.request.type == "message":
            print(f"User: {exchange.request.text}")
        for response in exchange.responses:
            if response.type == "message":
                print(f"Agent: {response.text}")

# Output:
# User: Hello
# Agent: Hi there! How can I help you?
# User: How are you?
# Agent: I'm doing great, thanks for asking!
# User: Goodbye
# Agent: Goodbye! Have a nice day!
```

---

### 🎬 `Scenario` — Test Infrastructure Made Easy

#### Testing an External Agent

```python
from microsoft_agents.testing import ExternalScenario, Check

# Test against a running agent
scenario = ExternalScenario("http://localhost:3978/api/messages")

@pytest.mark.agent_test(scenario)
class TestExternalAgent:
    
    @pytest.mark.asyncio
    async def test_greeting(self, conv):
        responses = await conv.say("Hi!")
        Check(responses).where(type="message").is_not_empty()
```

#### Testing In-Process with `AiohttpScenario`

Spin up your agent in the same process—no external server needed:

```python
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment, Check

async def init_my_agent(env: AgentEnvironment):
    """Initialize your agent with full access to internals."""
    
    @env.agent_application.activity("message")
    async def on_message(context):
        await context.send_activity(f"Echo: {context.activity.text}")

scenario = AiohttpScenario(init_my_agent)

@pytest.mark.agent_test(scenario)
class TestInProcessAgent:
    
    @pytest.mark.asyncio
    async def test_echo(self, conv):
        responses = await conv.say("Hello!")
        Check(responses).where(type="message").that(
            text=lambda x: "Echo: Hello!" in x
        )
```

---

### 🔬 Accessing Agent Internals — The Game Changer

One of the most powerful features of `AiohttpScenario` is direct access to your agent's internal components. This lets you verify not just *what* your agent says, but *how* it processes requests internally.

#### Available Internal Components

| Fixture | Description |
|---------|-------------|
| `agent_environment` | Full environment container |
| `agent_application` | The `AgentApplication` instance |
| `storage` | The `Storage` instance (state persistence) |
| `adapter` | The `ChannelServiceAdapter` |
| `connection_manager` | The `Connections` manager |

#### Verifying Internal State

```python
@pytest.mark.agent_test(scenario)
class TestAgentInternals:
    
    @pytest.mark.asyncio
    async def test_state_persisted_correctly(self, conv, storage):
        """Verify that conversation state is saved correctly."""
        await conv.say("Remember my favorite color is blue")
        
        # Directly inspect the storage layer
        state = await storage.read(["conversation_state"])
        assert "blue" in str(state).lower()
    
    @pytest.mark.asyncio
    async def test_user_profile_updated(self, conv, agent_application):
        """Verify user profile state after interaction."""
        await conv.say("My name is Alice and I'm from Seattle")
        
        # Access the application's state accessors directly
        # Verify the internal data structures match expectations
        assert agent_application is not None
    
    @pytest.mark.asyncio
    async def test_adapter_configuration(self, adapter, agent_environment):
        """Verify adapter is configured correctly for the scenario."""
        assert adapter is not None
        assert agent_environment.config is not None
```

#### Why This Matters

Traditional agent testing only lets you verify outputs—the messages your agent sends back. With internal access, you can:

- **Verify state persistence**: Ensure user preferences, conversation context, and session data are stored correctly
- **Test error recovery**: Confirm your agent's internal state is clean after handling errors
- **Validate business logic**: Check that internal flags, counters, or workflow states update as expected
- **Debug flaky tests**: Inspect exactly what your agent "remembers" at each step
- **Test authorization flows**: Verify tokens and credentials are handled properly

---

### 📝 `ActivityTemplate` — Consistent Test Data

Create activities with sensible defaults:

```python
from microsoft_agents.testing import ActivityTemplate

# Define a template with defaults
template = ActivityTemplate({
    "channel_id": "test",
    "locale": "en-US",
    "from.id": "test-user",
    "from.name": "Test User",
})

# Create activities from the template
activity = template.create({"text": "Hello"})
# → Activity with all template fields + text="Hello"
```

---

## Beyond Testing: Local Debugging & Exploration

The framework isn't just for automated tests—it's a powerful tool for local development and debugging.

### Interactive Agent Exploration

Use scenarios outside of pytest to explore your agent's behavior:

```python
import asyncio
from microsoft_agents.testing import ExternalScenario, print_messages

async def explore_agent():
    scenario = ExternalScenario("http://localhost:3978/api/messages")
    
    async with scenario.client() as client:
        # Have a conversation
        await client.send("What can you help me with?")
        await client.send("Tell me about your capabilities")
        await client.send("How do I get started?")
        
        # Review the full conversation
        print_messages(client.transcript)

asyncio.run(explore_agent())
```

### Debugging Response Timing

Investigate latency issues in your agent:

```python
async def analyze_response_times():
    scenario = ExternalScenario("http://localhost:3978/api/messages")
    
    async with scenario.client() as client:
        # Send messages and track timing
        exchanges = await client.ex_send("Simple greeting")
        if exchanges[0].latency_ms:
            print(f"Simple message: {exchanges[0].latency_ms:.2f}ms")
        
        exchanges = await client.ex_send("Complex query requiring database lookup")
        if exchanges[0].latency_ms:
            print(f"Complex query: {exchanges[0].latency_ms:.2f}ms")

asyncio.run(analyze_response_times())
```

### Prototyping Conversation Flows

Quickly prototype and validate conversation designs:

```python
async def prototype_onboarding_flow():
    scenario = ExternalScenario("http://localhost:3978/api/messages")
    
    async with scenario.client() as client:
        # Simulate the onboarding flow you're designing
        flows = [
            "Hi, I'm new here",
            "Yes, I'd like to set up my profile",
            "My name is Alex",
            "I prefer email notifications",
            "Thanks, that's all for now",
        ]
        
        for message in flows:
            responses = await client.send(message)
            print(f"\n> {message}")
            for r in responses:
                if r.type == "message":
                    print(f"  Bot: {r.text}")
        
        # Save transcript for review
        print("\n--- Full Transcript ---")
        print_messages(client.transcript)

asyncio.run(prototype_onboarding_flow())
```

### Reproducing Production Issues

Replay specific conversation patterns to reproduce bugs:

```python
async def reproduce_issue_12345():
    """Reproduce the bug where agent crashes on special characters."""
    scenario = ExternalScenario("http://localhost:3978/api/messages")
    
    async with scenario.client() as client:
        # The exact sequence that caused the issue
        problematic_inputs = [
            "Hello",
            "My email is test@example.com",
            "Here's some JSON: {\"key\": \"value\"}",  # This was causing issues
            "What happened?",
        ]
        
        for msg in problematic_inputs:
            try:
                exchanges = await client.ex_send(msg)
                exchange = exchanges[0]
                print(f"✓ '{msg[:30]}...' → Status: {exchange.status_code}")
            except Exception as e:
                print(f"✗ '{msg[:30]}...' → Error: {e}")

asyncio.run(reproduce_issue_12345())
```

---

## pytest Integration

The framework provides a pytest plugin with automatic fixtures:

```python
import pytest
from microsoft_agents.testing import Check

@pytest.mark.agent_test("http://localhost:3978/api/messages")
class TestMyAgent:
    
    @pytest.mark.asyncio
    async def test_with_conv(self, conv):
        """ConversationClient for high-level interaction."""
        responses = await conv.say("Hello")
        Check(responses).where(type="message").is_not_empty()
    
    @pytest.mark.asyncio
    async def test_with_agent_client(self, agent_client):
        """AgentClient for lower-level control."""
        await agent_client.send("Hello")
        transcript = agent_client.transcript
        assert len(transcript.get_all()) > 0
    
    @pytest.mark.asyncio
    async def test_with_environment(self, agent_environment):
        """Access agent internals (in-process scenarios only)."""
        storage = agent_environment.storage
        adapter = agent_environment.adapter
```

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `conv` | High-level `ConversationClient` |
| `agent_client` | Lower-level `AgentClient` |
| `agent_environment` | Access to agent internals (in-process only) |
| `agent_application` | The `AgentApplication` instance |
| `storage` | The `Storage` instance |
| `adapter` | The `ChannelServiceAdapter` instance |

---

## Common Patterns

### Testing Command-Based Agents

```python
@pytest.mark.agent_test(my_scenario)
class TestCommands:
    
    @pytest.mark.asyncio
    async def test_help_command(self, conv):
        responses = await conv.say("help")
        Check(responses).where(type="message").that(
            text=lambda x: "Available commands" in x
        )
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, conv):
        responses = await conv.say("foobar")
        Check(responses).where(type="message").that(
            text=lambda x: "Unknown command" in x
        )
```

### Validating Card Responses

```python
@pytest.mark.asyncio
async def test_returns_adaptive_card(self, conv):
    responses = await conv.say("show menu")
    
    # Check for card attachment
    Check(responses).where(type="message").that(
        attachments=lambda x: any(
            att.content_type == "application/vnd.microsoft.card.adaptive"
            for att in x
        )
    )
```

### Testing Error Handling

```python
@pytest.mark.asyncio
async def test_handles_invalid_input(self, conv):
    responses = await conv.say("!@#$%^&*()")
    
    # Should respond gracefully, not crash
    Check(responses).where(type="message").is_not_empty()
    Check(responses).where(type="message").that_for_none(
        text=lambda x: "error" in x.lower() or "exception" in x.lower()
    )
```

### Conversation State Verification

```python
@pytest.mark.asyncio
async def test_remembers_context(self, conv):
    await conv.say("My name is Alice")
    responses = await conv.say("What's my name?")
    
    Check(responses).where(type="message").that(
        text=lambda x: "Alice" in x
    )
```

### Waiting for Slow Operations

```python
@pytest.mark.asyncio
async def test_long_running_task(self, conv):
    conv.timeout = 30.0  # Give it time
    
    await conv.say("Generate a detailed report")
    
    # Wait for the typing indicator first
    await conv.expect(type="typing")
    
    # Then wait for the final response
    responses = await conv.wait_for(
        type="message",
        text=lambda x: "Report" in x and len(x) > 500
    )
    
    Check(responses).where(type="message").last().that(
        text=lambda actual, root: (
            "Report" in actual and 
            root.attachments is not None
        )
    )
```

---

## API Summary

| Component | Purpose |
|-----------|---------|
| `Check` | Fluent filtering and assertions on responses |
| `ConversationClient` | High-level conversation helper with `say`, `wait_for`, `expect` |
| `AgentClient` | Low-level activity sending with full control |
| `Transcript` | Complete conversation history tracking |
| `Exchange` | Single request-response pair with metadata |
| `Scenario` | Test infrastructure management |
| `ExternalScenario` | Test against running agents |
| `AiohttpScenario` | In-process agent testing |
| `ActivityTemplate` | Create activities with defaults |
| `ClientConfig` | Configure client identity and headers |

---

## Coming Soon

We're actively developing new features to make agent testing even more powerful:

### 🖥️ CLI Tools
- **`agents-test chat`** — Interactive terminal chat with your agent for quick manual testing
- **`agents-test validate`** — Validate your environment configuration and connectivity
- **`agents-test run`** — Run predefined test scenarios from the command line

### 📡 Streaming Support
- **`agent_client.send_stream()`** — Handle streaming responses for agents that send incremental updates
- Real-time assertion support for streaming content

### 📊 Enhanced Transcript Utilities
- **Export formats** — Save transcripts as JSON, Markdown, or HTML for documentation and review
- **Transcript comparison** — Diff two transcripts to detect behavioral regressions
- **Transcript replay** — Replay recorded conversations against updated agents
- **Analytics helpers** — Aggregate latency stats, response patterns, and error rates

### 🧪 Advanced Testing Scenarios
- **Multi-user simulation** — Test concurrent conversations with multiple simulated users
- **Chaos testing** — Inject network delays, timeouts, and errors to test resilience
- **Load testing utilities** — Simple patterns for testing agent performance under load

### 🔍 Improved Assertions
- **Semantic matching** — Assert on meaning rather than exact text (e.g., "response is a greeting")
- **Schema validation** — Validate adaptive card and attachment structures
- **Conversation flow assertions** — Assert on the overall shape of a multi-turn conversation

---

## License

MIT License - Microsoft Corporation
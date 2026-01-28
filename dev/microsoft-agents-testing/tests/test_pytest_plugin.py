# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Integration Tests for the pytest_plugin module.

This module provides real integration tests demonstrating the full capabilities
of the Microsoft Agents Testing framework, integrating:
- Scenario: AiohttpScenario for in-process agent hosting
- Client: AgentClient and ConversationClient for agent communication  
- Check: Unified assertion and selection API for response validation

These tests also serve as documentation for library users, showing common
usage patterns and best practices.

=============================================================================
USAGE PATTERNS DEMONSTRATED
=============================================================================

1. Basic @pytest.mark.agent_test usage with AiohttpScenario
2. Using the `conv` fixture for high-level conversation testing
3. Using the `agent_client` fixture for low-level activity control
4. Accessing agent environment via `agent_environment` fixture
5. Multi-user conversation testing
6. Response validation with the Check API
7. Working with transcripts and exchanges
8. Testing different activity types (message, typing indicators, etc.)
"""

import pytest
from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.testing.check import Check
from microsoft_agents.testing.scenario import (
    AiohttpScenario,
    ScenarioConfig,
    ClientConfig,
    AgentEnvironment,
)
from microsoft_agents.testing.client import AgentClient, ConversationClient


# =============================================================================
# Sample Agent Initializers
# =============================================================================

async def echo_agent_init(env: AgentEnvironment) -> None:
    """
    Initialize a simple echo agent.
    
    This agent echoes back the user's message with an "Echo: " prefix.
    """
    @env.agent_application.activity("message")
    async def on_message(context, state):
        await context.send_activity(f"Echo: {context.activity.text}")


async def greeting_agent_init(env: AgentEnvironment) -> None:
    """
    Initialize a greeting agent.
    
    This agent greets the user by name (from activity.from_property.name).
    """
    @env.agent_application.activity("message")
    async def on_message(context, state):
        user_name = context.activity.from_property.name or "User"
        await context.send_activity(f"Hello, {user_name}!")


async def multi_response_agent_init(env: AgentEnvironment) -> None:
    """
    Initialize an agent that sends multiple responses.
    
    This agent responds with a typing indicator followed by a message.
    """
    @env.agent_application.activity("message")
    async def on_message(context, state):
        # Send typing indicator first
        await context.send_activity(Activity(type=ActivityTypes.typing))
        # Then send the actual response
        await context.send_activity(f"Processed: {context.activity.text}")


async def stateful_agent_init(env: AgentEnvironment) -> None:
    """
    Initialize a stateful agent that tracks message count.
    
    This agent uses storage to count messages per conversation.
    """
    @env.agent_application.activity("message")
    async def on_message(context, state):
        # Simple counter using state
        count = state.conversation.get_value("count") or 0
        count += 1
        state.conversation.set_value("count", count)
        await context.send_activity(f"Message #{count}: {context.activity.text}")


async def help_agent_init(env: AgentEnvironment) -> None:
    """
    Initialize an agent that responds to specific commands.
    
    Responds to:
    - "help" with usage instructions
    - "ping" with "pong"
    - Other messages with a generic response
    """
    @env.agent_application.activity("message")
    async def on_message(context, state):
        text = (context.activity.text or "").lower().strip()
        
        if text == "help":
            await context.send_activity(
                "Available commands:\n- help: Show this message\n- ping: Test connectivity"
            )
        elif text == "ping":
            await context.send_activity("pong")
        else:
            await context.send_activity(f"Unknown command: {context.activity.text}")


# =============================================================================
# Scenario Fixtures for Tests
# =============================================================================

echo_scenario = AiohttpScenario(
    init_agent=echo_agent_init,
    use_jwt_middleware=False,
)

greeting_scenario = AiohttpScenario(
    init_agent=greeting_agent_init,
    use_jwt_middleware=False,
)

multi_response_scenario = AiohttpScenario(
    init_agent=multi_response_agent_init,
    use_jwt_middleware=False,
)

stateful_scenario = AiohttpScenario(
    init_agent=stateful_agent_init,
    use_jwt_middleware=False,
)

help_scenario = AiohttpScenario(
    init_agent=help_agent_init,
    use_jwt_middleware=False,
)


# =============================================================================
# Basic @pytest.mark.agent_test Usage
# =============================================================================

@pytest.mark.agent_test(echo_scenario)
class TestBasicAgentTestMarker:
    """
    Demonstrates basic usage of @pytest.mark.agent_test marker.
    
    The marker sets up the agent scenario and provides fixtures:
    - conv: ConversationClient for high-level message sending
    - agent_client: AgentClient for low-level activity control
    """
    
    @pytest.mark.asyncio
    async def test_send_message_and_receive_response(self, conv: ConversationClient):
        """
        Basic test: send a message and verify we get a response.
        
        This is the simplest usage pattern - send a message with `conv.say()`
        and verify the response contains expected text.
        """
        responses = await conv.say("Hello, Agent!", wait=0.1)
        
        # Filter to message activities (real agents may send typing first)
        messages = Check(responses).where(type="message")
        
        # Verify we got at least one message response
        messages.is_not_empty()
        
        # Verify the echo response
        messages.last().that(text=lambda x: "Echo:" in x and "Hello, Agent!" in x)
    
    @pytest.mark.asyncio
    async def test_multiple_messages_in_conversation(self, conv: ConversationClient):
        """
        Test sending multiple messages in the same conversation.
        
        Each message should be echoed back independently.
        """
        response1 = await conv.say("First message", wait=0.1)
        response2 = await conv.say("Second message", wait=0.1)
        
        # Filter to message activities and check last message in each response
        Check(response1).where(type="message").last().that(
            text=lambda x: "First message" in x
        )
        Check(response2).where(type="message").last().that(
            text=lambda x: "Second message" in x
        )


# =============================================================================
# Using Check API for Response Validation
# =============================================================================

@pytest.mark.agent_test(echo_scenario)
class TestCheckApiIntegration:
    """
    Demonstrates using the Check API for response validation.
    
    The Check class provides a fluent API for:
    - Filtering responses with `where()`
    - Asserting conditions with `that()`
    - Quantified assertions with `that_for_any()`, `that_for_all()`, etc.
    """
    
    @pytest.mark.asyncio
    async def test_check_where_filter(self, conv: ConversationClient):
        """
        Use Check.where() to filter responses by type.
        """
        responses = await conv.say("Test message", wait=0.1)
        
        # Filter to only message activities
        messages = Check(responses).where(type="message")
        
        messages.is_not_empty()
        messages.that(type="message")
    
    @pytest.mark.asyncio
    async def test_check_that_assertion(self, conv: ConversationClient):
        """
        Use Check.that() to assert all items match a condition.
        """
        responses = await conv.say("Validation test", wait=0.1)
        
        # Assert all message responses contain expected text
        Check(responses).where(type="message").that(
            text=lambda x: "Echo:" in x
        )
    
    @pytest.mark.asyncio
    async def test_check_that_for_any(self, conv: ConversationClient):
        """
        Use Check.that_for_any() to assert at least one item matches.
        """
        responses = await conv.say("Check any", wait=0.1)
        
        # Assert at least one response contains the text
        Check(responses).that_for_any(
            text=lambda x: "Check any" in x if x else False
        )
    
    @pytest.mark.asyncio
    async def test_check_count_and_empty(self, conv: ConversationClient):
        """
        Use Check terminal operations: count(), empty(), is_not_empty().
        """
        responses = await conv.say("Count test", wait=0.1)
        
        check = Check(responses).where(type="message")
        
        # Terminal operations
        assert check.count() > 0
        assert not check.empty()
        check.is_not_empty()  # Assertion method
    
    @pytest.mark.asyncio
    async def test_check_first_and_last(self, conv: ConversationClient):
        """
        Use Check.first() and Check.last() for position-based selection.
        """
        responses = await conv.say("Position test", wait=0.1)
        
        messages = Check(responses).where(type="message")
        
        # Get first and last message
        first = messages.first().get()
        last = messages.last().get()
        
        assert len(first) <= 1
        assert len(last) <= 1


# =============================================================================
# Using agent_client for Low-Level Control
# =============================================================================


def get_message_responses_from_exchanges(exchanges: list) -> list[Activity]:
    """
    Helper to extract message activities from exchanges.
    
    Exchanges may contain typing indicators or other non-message activities.
    This helper flattens all responses and filters to message activities only.
    """
    all_responses = []
    for exchange in exchanges:
        if hasattr(exchange, 'responses') and exchange.responses:
            all_responses.extend(exchange.responses)
    return Check(all_responses).where(type="message").get()


@pytest.mark.agent_test(echo_scenario)
class TestAgentClientLowLevel:
    """
    Demonstrates using agent_client for low-level activity control.
    
    AgentClient provides:
    - send(): Send activity and get response activities
    - ex_send(): Send activity and get exchanges (includes metadata)
    - send_expect_replies(): Use expect_replies delivery mode
    - invoke(): Send invoke activities
    """
    
    @pytest.mark.asyncio
    async def test_send_string_message(self, agent_client: AgentClient):
        """
        Send a string message (auto-converted to Activity).
        """
        responses = await agent_client.send("Hello", wait=0.1)
        
        # Filter to message activities and verify echo
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: "Echo: Hello" in x
        )
    
    @pytest.mark.asyncio
    async def test_send_activity_object(self, agent_client: AgentClient):
        """
        Send a fully constructed Activity object.
        """
        activity = Activity(
            type=ActivityTypes.message,
            text="Custom activity"
        )
        
        responses = await agent_client.send(activity, wait=0.1)
        
        # Filter to message activities and verify response
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: "Custom activity" in x
        )
    
    @pytest.mark.asyncio
    async def test_ex_send_returns_exchanges(self, agent_client: AgentClient):
        """
        Use ex_send() to get Exchange objects with full metadata.
        
        Exchange includes:
        - request: The sent activity
        - responses: List of received activities  
        - status_code: HTTP response status
        - latency_ms: Request latency in milliseconds
        """
        exchanges = await agent_client.ex_send("Exchange test", wait=0.1)
        
        # Extract message responses (filtering out typing indicators)
        message_responses = get_message_responses_from_exchanges(exchanges)
        Check(message_responses).is_not_empty()
        Check(message_responses).last().that(
            text=lambda x: "Echo: Exchange test" in x
        )
    
    @pytest.mark.asyncio
    async def test_transcript_access(self, agent_client: AgentClient):
        """
        Access the transcript to review all exchanges.
        """
        await agent_client.send("First", wait=0.1)
        await agent_client.send("Second", wait=0.1)
        
        # Get all exchanges from transcript
        all_exchanges = agent_client.transcript.get_all()
        
        assert len(all_exchanges) >= 2
        
        # Verify message responses exist in the exchanges (filtering out typing)
        message_responses = get_message_responses_from_exchanges(all_exchanges)
        Check(message_responses).is_not_empty()
        
        # Verify both messages were echoed
        Check(message_responses).that_for_any(
            text=lambda x: "First" in x if x else False
        )
        Check(message_responses).that_for_any(
            text=lambda x: "Second" in x if x else False
        )


# =============================================================================
# Testing with Custom User Configuration
# =============================================================================

custom_user_scenario = AiohttpScenario(
    init_agent=greeting_agent_init,
    config=ScenarioConfig(
        client_config=ClientConfig(
            user_id="alice",
            user_name="Alice Smith"
        )
    ),
    use_jwt_middleware=False,
)


@pytest.mark.agent_test(custom_user_scenario)
class TestCustomUserConfiguration:
    """
    Demonstrates testing with custom user configuration.
    
    The user identity is passed to the agent in activity.from_property.
    """
    
    @pytest.mark.asyncio
    async def test_agent_receives_user_name(self, conv: ConversationClient):
        """
        Verify the agent receives the configured user name.
        """
        responses = await conv.say("Hi!", wait=0.1)
        
        # Filter to message activities (real agents may send typing first)
        # Greeting agent should greet Alice by name
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: "Alice" in x
        )


# =============================================================================
# Testing Multi-Response Agents
# =============================================================================

@pytest.mark.agent_test(multi_response_scenario)
class TestMultiResponseAgent:
    """
    Demonstrates testing agents that send multiple activities.
    
    Some agents send typing indicators, proactive messages, or
    multiple sequential responses.
    """
    
    @pytest.mark.asyncio
    async def test_receives_typing_and_message(self, conv: ConversationClient):
        """
        Verify we receive both typing indicator and message.
        """
        responses = await conv.say("Multi-response test", wait=0.2)
        
        # Should have at least 2 responses (typing + message)
        assert len(responses) >= 2
        
        # Check for typing activity
        Check(responses).where(type="typing").is_not_empty()
        
        # Check for message activity
        Check(responses).where(type="message").is_not_empty()
    
    @pytest.mark.asyncio  
    async def test_filter_to_messages_only(self, conv: ConversationClient):
        """
        Use Check to filter out non-message activities.
        """
        responses = await conv.say("Filter test", wait=0.2)
        
        # Get only message activities for assertion
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").that(
            text=lambda x: "Processed:" in x if x else False
        )


# =============================================================================
# Testing Command-Based Agents
# =============================================================================

@pytest.mark.agent_test(help_scenario)
class TestCommandBasedAgent:
    """
    Demonstrates testing agents with command handling.
    
    Tests verify different code paths based on user input.
    """
    
    @pytest.mark.asyncio
    async def test_help_command(self, conv: ConversationClient):
        """Test the help command returns usage instructions."""
        responses = await conv.say("help", wait=0.1)
        
        # Filter to message activities and check content
        messages = Check(responses).where(type="message")
        messages.is_not_empty()
        
        messages.last().that(
            text=lambda x: "Available commands" in x and "help" in x and "ping" in x
        )
    
    @pytest.mark.asyncio
    async def test_ping_command(self, conv: ConversationClient):
        """Test the ping command returns pong."""
        responses = await conv.say("ping", wait=0.1)
        
        # Filter to message activities and verify exact response
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(text="pong")
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, conv: ConversationClient):
        """Test unknown commands get appropriate response."""
        responses = await conv.say("foobar", wait=0.1)
        
        # Filter to message activities and verify response
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: "Unknown command" in x and "foobar" in x
        )
    
    @pytest.mark.asyncio
    async def test_case_insensitive_commands(self, conv: ConversationClient):
        """Test that commands are case-insensitive."""
        responses_upper = await conv.say("HELP", wait=0.1)
        responses_mixed = await conv.say("HeLp", wait=0.1)
        
        # Both should return help text - filter to messages first
        Check(responses_upper).where(type="message").last().that(
            text=lambda x: "Available commands" in x
        )
        Check(responses_mixed).where(type="message").last().that(
            text=lambda x: "Available commands" in x
        )


# =============================================================================
# Accessing Agent Environment (In-Process Scenarios Only)
# =============================================================================

@pytest.mark.agent_test(echo_scenario)
class TestAgentEnvironmentAccess:
    """
    Demonstrates accessing agent environment components.
    
    Only available for in-process scenarios (AiohttpScenario), not
    for ExternalScenario. Provides access to:
    - agent_application
    - storage
    - adapter
    - authorization
    - connections
    """
    
    @pytest.mark.asyncio
    async def test_access_agent_application(
        self, 
        agent_environment: AgentEnvironment,
        conv: ConversationClient
    ):
        """Access the AgentApplication instance."""
        assert agent_environment.agent_application is not None
        
        # Can still use conv normally
        responses = await conv.say("Environment test", wait=0.1)
        Check(responses).where(type="message").is_not_empty()
    
    @pytest.mark.asyncio
    async def test_access_storage(self, agent_environment: AgentEnvironment):
        """Access the Storage instance for state inspection."""
        assert agent_environment.storage is not None
    
    @pytest.mark.asyncio
    async def test_access_adapter(self, agent_environment: AgentEnvironment):
        """Access the ChannelServiceAdapter instance."""
        assert agent_environment.adapter is not None


# =============================================================================
# Advanced Check API Patterns
# =============================================================================

@pytest.mark.agent_test(echo_scenario)
class TestAdvancedCheckPatterns:
    """
    Demonstrates advanced Check API usage patterns.
    """
    
    @pytest.mark.asyncio
    async def test_check_with_callable_predicate(self, conv: ConversationClient):
        """
        Use callable predicates for complex assertions.
        """
        responses = await conv.say("Predicate test", wait=0.1)
        
        # Custom predicate function
        def has_echo_prefix(x):
            return x is not None and x.startswith("Echo:")
        
        Check(responses).where(type="message").that(text=has_echo_prefix)
    
    @pytest.mark.asyncio
    async def test_check_where_not(self, conv: ConversationClient):
        """
        Use where_not() to exclude items.
        """
        responses = await conv.say("Exclusion test", wait=0.1)
        
        # Exclude typing activities
        non_typing = Check(responses).where_not(type="typing")
        
        non_typing.that_for_all(type=lambda x: x != "typing")
    
    @pytest.mark.asyncio
    async def test_check_chaining(self, conv: ConversationClient):
        """
        Chain multiple Check operations.
        """
        responses = await conv.say("Chain test", wait=0.1)
        
        result = (
            Check(responses)
            .where(type="message")
            .where(text=lambda x: "Chain" in x if x else False)
            .first()
            .get()
        )
        
        assert len(result) <= 1
    
    @pytest.mark.asyncio
    async def test_check_quantified_assertions(self, conv: ConversationClient):
        """
        Use quantified assertions for flexible validation.
        """
        responses = await conv.say("Quantified test", wait=0.1)
        
        # For all messages, text should not be None
        Check(responses).where(type="message").that_for_all(
            text=lambda x: x is not None
        )
        
        # At least one response should contain "Echo"
        Check(responses).that_for_any(
            text=lambda x: "Echo" in x if x else False
        )


# =============================================================================
# Testing Stateful Conversations
# =============================================================================

@pytest.mark.agent_test(stateful_scenario)
class TestStatefulConversation:
    """
    Demonstrates testing stateful agents that maintain conversation state.
    """
    
    @pytest.mark.asyncio
    async def test_message_counter_increments(self, conv: ConversationClient):
        """
        Verify stateful agent tracks message count correctly.
        """
        response1 = await conv.say("First", wait=0.1)
        response2 = await conv.say("Second", wait=0.1)
        response3 = await conv.say("Third", wait=0.1)
        
        # Each response should have incrementing message number
        # Filter to message activities to handle potential typing indicators
        Check(response1).where(type="message").last().that(
            text=lambda x: "Message #1" in x
        )
        Check(response2).where(type="message").last().that(
            text=lambda x: "Message #2" in x
        )
        Check(response3).where(type="message").last().that(
            text=lambda x: "Message #3" in x
        )


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================

@pytest.mark.agent_test(echo_scenario)
class TestErrorHandlingAndEdgeCases:
    """
    Demonstrates handling edge cases and error conditions.
    """
    
    @pytest.mark.asyncio
    async def test_empty_message(self, conv: ConversationClient):
        """Test sending an empty message."""
        responses = await conv.say("", wait=0.1)
        
        # Agent should still respond - filter to message activities
        Check(responses).where(type="message").is_not_empty()
    
    @pytest.mark.asyncio
    async def test_long_message(self, conv: ConversationClient):
        """Test sending a very long message."""
        long_text = "A" * 1000
        responses = await conv.say(long_text, wait=0.1)
        
        # Filter to message activities and verify echo contains the long text
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: long_text in x
        )
    
    @pytest.mark.asyncio
    async def test_special_characters(self, conv: ConversationClient):
        """Test messages with special characters."""
        special_text = "Hello! @#$%^&*() 🎉 émojis"
        responses = await conv.say(special_text, wait=0.1)
        
        # Filter to message activities and verify echo contains special chars
        Check(responses).where(type="message").is_not_empty()
        Check(responses).where(type="message").last().that(
            text=lambda x: special_text in x
        )


# =============================================================================
# Function-Level Test Decoration
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.agent_test(echo_scenario)
async def test_function_level_marker(conv: ConversationClient):
    """
    Demonstrates @pytest.mark.agent_test on a function (not class).
    
    The marker works on both test classes and individual test functions.
    """
    responses = await conv.say("Function test", wait=0.1)
    
    # Filter to message activities and verify response
    Check(responses).where(type="message").is_not_empty()
    Check(responses).where(type="message").last().that(
        text=lambda x: "Echo: Function test" in x
    )


@pytest.mark.asyncio
@pytest.mark.agent_test(greeting_scenario)
async def test_different_scenario_per_function(conv: ConversationClient):
    """
    Different functions can use different scenarios.
    """
    responses = await conv.say("Hi!", wait=0.1)
    
    # This uses greeting_scenario, not echo_scenario
    # Filter to message activities to handle potential typing indicators
    Check(responses).where(type="message").is_not_empty()
    Check(responses).where(type="message").last().that(
        text=lambda x: "Hello" in x
    )
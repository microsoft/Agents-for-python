# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Integration tests for AiohttpScenario with actual agent definitions.

These tests demonstrate real agent testing using AiohttpScenario with:
- Real AgentApplication instances
- Real message handlers
- Real HTTP communication (via aiohttp.test_utils.TestServer)
- Fluent assertions using Expect and Select classes
- No mocks - actual agent behavior is tested

JWT middleware is disabled for simplicity in these tests.
"""

import pytest

from microsoft_agents.activity import Activity, ActivityTypes, EndOfConversationCodes
from microsoft_agents.hosting.core import TurnContext, TurnState

from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment
from microsoft_agents.testing.core import ScenarioConfig
from microsoft_agents.testing.core.fluent import Expect, Select


# ============================================================================
# Simple Echo Agent Tests
# ============================================================================


class TestEchoAgent:
    """Integration tests with a simple echo agent."""

    @pytest.mark.asyncio
    async def test_echo_agent_responds_to_message(self):
        """Echo agent echoes back the user's message."""

        async def init_echo_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(f"Echo: {context.activity.text}")

        scenario = AiohttpScenario(
            init_agent=init_echo_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("Hello, Agent!", wait=.2)
            client.expect().that_for_any(text="Echo: Hello, Agent!")

    @pytest.mark.asyncio
    async def test_echo_agent_handles_multiple_messages(self):
        """Echo agent handles multiple sequential messages."""

        async def init_echo_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(f"Echo: {context.activity.text}")

        scenario = AiohttpScenario(
            init_agent=init_echo_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("First message")
            await client.send("Second message")
            await client.send("Third message")

            client.expect().that_for_exactly(3, type=ActivityTypes.message)
            client.expect().that_for_any(text="Echo: First message")
            client.expect().that_for_any(text="Echo: Second message")
            client.expect().that_for_any(text="Echo: Third message")

    @pytest.mark.asyncio
    async def test_echo_agent_with_empty_message(self):
        """Echo agent handles empty message text."""

        async def init_echo_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                text = context.activity.text or ""
                await context.send_activity(f"Echo: {text}")

        scenario = AiohttpScenario(
            init_agent=init_echo_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("")

            client.expect().that_for_any(text="Echo: ")


# ============================================================================
# Multi-Response Agent Tests
# ============================================================================


class TestMultiResponseAgent:
    """Integration tests with an agent that sends multiple responses."""

    @pytest.mark.asyncio
    async def test_agent_sends_multiple_activities(self):
        """Agent can send multiple activities in response."""

        async def init_multi_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("First response")
                await context.send_activity("Second response")
                await context.send_activity("Third response")

        scenario = AiohttpScenario(
            init_agent=init_multi_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("trigger", wait=1.0)

            # Verify all three responses exist
            client.expect().that_for_any(text="First response")
            client.expect().that_for_any(text="Second response")
            client.expect().that_for_any(text="Third response")

    @pytest.mark.asyncio
    async def test_agent_sends_typing_then_message(self):
        """Agent can send typing indicator followed by message."""

        async def init_typing_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(Activity(type=ActivityTypes.typing))
                await context.send_activity("Here is my response!")

        scenario = AiohttpScenario(
            init_agent=init_typing_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("Hello", wait=1.0)

            # Should have both typing and message activities
            client.expect().that_for_any(type=ActivityTypes.typing)
            client.expect().that_for_any(type=ActivityTypes.message, text="Here is my response!")


# ============================================================================
# Command Router Agent Tests
# ============================================================================


class TestCommandRouterAgent:
    """Integration tests with an agent that routes different commands."""

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Agent responds to /help command."""

        async def init_router_agent(env: AgentEnvironment) -> None:
            @env.agent_application.message("/help")
            async def on_help(context: TurnContext, state: TurnState):
                await context.send_activity(
                    "Available commands: /help, /status, /echo <text>"
                )

            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(f"Unknown command: {context.activity.text}")

        scenario = AiohttpScenario(
            init_agent=init_router_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("/help")

            client.expect().that_for_any(text="~Available commands")

    @pytest.mark.asyncio
    async def test_multiple_commands(self):
        """Agent routes multiple different commands correctly."""

        async def init_router_agent(env: AgentEnvironment) -> None:
            @env.agent_application.message("/hello")
            async def on_hello(context: TurnContext, state: TurnState):
                await context.send_activity("Hello there!")

            @env.agent_application.message("/bye")
            async def on_bye(context: TurnContext, state: TurnState):
                await context.send_activity("Goodbye!")

            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("I don't understand.")

        scenario = AiohttpScenario(
            init_agent=init_router_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("/hello")
            client.expect().that_for_any(text="Hello there!")

            client.clear()
            await client.send("/bye")
            client.expect().that_for_any(text="Goodbye!")

            client.clear()
            await client.send("random text")
            client.expect().that_for_any(text="I don't understand.")


# ============================================================================
# Stateful Agent Tests
# ============================================================================


class TestStatefulAgent:
    """Integration tests with an agent that maintains state."""

    @pytest.mark.asyncio
    async def test_agent_tracks_message_count(self):
        """Agent tracks how many messages it has received."""
        message_count = {"count": 0}

        async def init_counter_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                message_count["count"] += 1
                await context.send_activity(f"Message #{message_count['count']}")

        scenario = AiohttpScenario(
            init_agent=init_counter_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("First")
            await client.send("Second")
            await client.send("Third")

            client.expect().that_for_any(text="Message #1")
            client.expect().that_for_any(text="Message #2")
            client.expect().that_for_any(text="Message #3")

    @pytest.mark.asyncio
    async def test_agent_remembers_last_message(self):
        """Agent remembers the last message sent."""
        state = {"last_message": None}

        async def init_memory_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state_param: TurnState):
                if state["last_message"]:
                    await context.send_activity(
                        f"Your last message was: {state['last_message']}"
                    )
                else:
                    await context.send_activity("This is your first message!")
                state["last_message"] = context.activity.text

        scenario = AiohttpScenario(
            init_agent=init_memory_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("Hello")
            client.expect().that_for_any(text="This is your first message!")

            client.clear()
            await client.send("World")
            client.expect().that_for_any(text="Your last message was: Hello")

            client.clear()
            await client.send("Again")
            client.expect().that_for_any(text="Your last message was: World")


# ============================================================================
# End of Conversation Tests
# ============================================================================


class TestEndOfConversationAgent:
    """Integration tests with an agent that ends conversations."""

    @pytest.mark.asyncio
    async def test_agent_ends_conversation_on_bye(self):
        """Agent sends EndOfConversation activity on /bye command."""

        async def init_eoc_agent(env: AgentEnvironment) -> None:
            @env.agent_application.message("/bye")
            async def on_bye(context: TurnContext, state: TurnState):
                await context.send_activity("Goodbye!")
                await context.send_activity(
                    Activity(
                        type=ActivityTypes.end_of_conversation,
                        code=EndOfConversationCodes.completed_successfully,
                    )
                )

            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("Hello! Say /bye to end.")

        scenario = AiohttpScenario(
            init_agent=init_eoc_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("/bye", wait=1.0)

            client.expect().that_for_any(type=ActivityTypes.end_of_conversation)


# ============================================================================
# Select and Filter Tests
# ============================================================================


class TestSelectAndFilter:
    """Integration tests demonstrating Select for filtering responses."""

    @pytest.mark.asyncio
    async def test_select_only_message_activities(self):
        """Use Select to filter only message activities."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(Activity(type=ActivityTypes.typing))
                await context.send_activity("Response 1")
                await context.send_activity("Response 2")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test", wait=1.0)

            # Filter to only message activities
            messages = client.select().where(type=ActivityTypes.message)
            messages.expect().is_not_empty()
            messages.expect().that_for_any(text="Response 1")
            messages.expect().that_for_any(text="Response 2")

    @pytest.mark.asyncio
    async def test_select_first_and_last(self):
        """Use Select to get first and last responses."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("First")
                await context.send_activity("Middle")
                await context.send_activity("Last")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test", wait=1.0)

            messages = client.select().where(type=ActivityTypes.message)

            # Verify first and last
            messages.first().expect().that(text="First")
            messages.last().expect().that(text="Last")

    @pytest.mark.asyncio
    async def test_select_where_not(self):
        """Use Select.where_not to exclude certain activities."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity(Activity(type=ActivityTypes.typing))
                await context.send_activity("Hello!")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test", wait=1.0)

            # Exclude typing activities
            non_typing = client.select().where_not(type=ActivityTypes.typing)
            non_typing.expect().that(type=ActivityTypes.message)


# ============================================================================
# Agent Environment Access Tests
# ============================================================================


class TestAgentEnvironmentAccess:
    """Integration tests verifying agent_environment property during run."""

    @pytest.mark.asyncio
    async def test_agent_environment_available_during_run(self):
        """agent_environment is accessible during scenario.run()."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("OK")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.run() as factory:
            env = scenario.agent_environment

            assert env.agent_application is not None
            assert env.storage is not None
            assert env.adapter is not None
            assert env.authorization is not None
            assert env.connections is not None

    @pytest.mark.asyncio
    async def test_agent_environment_has_working_storage(self):
        """AgentEnvironment contains initialized storage."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.run() as factory:
            storage = scenario.agent_environment.storage

            # Verify storage exists and is the right type
            assert storage is not None


# ============================================================================
# Multiple Client Tests
# ============================================================================


class TestMultipleClients:
    """Integration tests with multiple clients in a single scenario."""

    @pytest.mark.asyncio
    async def test_multiple_clients_in_same_run(self):
        """Multiple clients can be created in a single run()."""
        messages_received = []

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                messages_received.append(context.activity.text)
                user_id = context.activity.from_property.id if context.activity.from_ else "unknown"
                await context.send_activity(f"Hello, {user_id}!")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.run() as factory:
            client1 = await factory()
            client2 = await factory()

            await client1.send("From client 1")
            await client2.send("From client 2")

            assert "From client 1" in messages_received
            assert "From client 2" in messages_received


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Integration tests for agent error handling."""

    @pytest.mark.asyncio
    async def test_agent_with_error_handler(self):
        """Agent error handler catches exceptions."""
        errors_caught = []

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                if context.activity.text == "crash":
                    raise ValueError("Intentional error")
                await context.send_activity("OK")

            @env.agent_application.error
            async def on_error(context: TurnContext, error: Exception):
                errors_caught.append(str(error))
                await context.send_activity("An error occurred")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("hello")
            client.expect().that_for_any(text="OK")

            client.clear()
            await client.send("crash")
            client.expect().that_for_any(text="An error occurred")

            assert len(errors_caught) == 1
            assert "Intentional error" in errors_caught[0]


# ============================================================================
# Custom ScenarioConfig Tests
# ============================================================================


class TestCustomScenarioConfig:
    """Integration tests with custom scenario configuration."""

    @pytest.mark.asyncio
    async def test_scenario_with_custom_callback_port(self):
        """Scenario works with custom callback server port."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("Custom port works!")

        config = ScenarioConfig(callback_server_port=9555)
        scenario = AiohttpScenario(
            init_agent=init_agent,
            config=config,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test")

            client.expect().that_for_any(text="Custom port works!")


# ============================================================================
# Expect Quantifier Tests
# ============================================================================


class TestExpectQuantifiers:
    """Integration tests demonstrating different Expect quantifiers."""

    @pytest.mark.asyncio
    async def test_that_for_all_messages_have_type(self):
        """All responses should have the message type."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("Response 1")
                await context.send_activity("Response 2")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test", wait=1.0)

            # All activities in history should be messages
            messages = client.select().where(type=ActivityTypes.message)
            messages.expect().that_for_all(type=ActivityTypes.message)

    @pytest.mark.asyncio
    async def test_that_for_none_are_errors(self):
        """No responses should be error types."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("Success!")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test")

            # No activities should have "error" in text
            client.expect().that_for_none(text="~error")

    @pytest.mark.asyncio
    async def test_that_for_one_matches(self):
        """Exactly one response matches criteria."""

        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity("message")
            async def on_message(context: TurnContext, state: TurnState):
                await context.send_activity("Hello!")
                await context.send_activity("Goodbye!")

        scenario = AiohttpScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("test", wait=1.0)

            client.expect().that_for_one(text="Hello!")
            client.expect().that_for_one(text="Goodbye!")

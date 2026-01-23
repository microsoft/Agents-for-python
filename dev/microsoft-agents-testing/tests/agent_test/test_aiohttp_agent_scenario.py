# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext, TurnState

from microsoft_agents.testing.agent_test.aiohttp_agent_scenario import (
    AiohttpAgentScenario,
    AgentEnvironment,
)
from microsoft_agents.testing.agent_test.agent_scenario import _HostedAgentScenario
from microsoft_agents.testing.agent_test.agent_scenario_config import AgentScenarioConfig
from microsoft_agents.testing.agent_test.agent_client import AgentClient


class TestAiohttpAgentScenarioValidation:
    """Test input validation for AiohttpAgentScenario."""

    def test_raises_when_init_agent_not_provided(self):
        """Test that initialization raises ValueError when init_agent is not provided."""
        with pytest.raises(ValueError, match="init_agent must be provided"):
            AiohttpAgentScenario(init_agent=None)

    def test_inherits_from_hosted_agent_scenario(self):
        """Test that AiohttpAgentScenario inherits from _HostedAgentScenario."""
        assert issubclass(AiohttpAgentScenario, _HostedAgentScenario)


class TestAiohttpAgentScenarioIntegration:
    """Integration tests for AiohttpAgentScenario.
    
    These tests use real SDK components with JWT middleware disabled.
    """

    @pytest.mark.asyncio
    async def test_client_yields_agent_client(self):
        """Test that the client context manager yields an AgentClient."""
        async def init_agent(env: AgentEnvironment):
            pass

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            assert isinstance(client, AgentClient)

    @pytest.mark.asyncio
    async def test_init_agent_receives_complete_environment(self):
        """Test that init_agent receives an environment with all required components."""
        received_env = None

        async def init_agent(env: AgentEnvironment):
            nonlocal received_env
            received_env = env

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            assert received_env is not None
            assert received_env.agent_application is not None
            assert received_env.authorization is not None
            assert received_env.adapter is not None
            assert received_env.storage is not None
            assert received_env.connections is not None
            assert received_env.config is not None

    @pytest.mark.asyncio
    async def test_agent_environment_accessible_after_client_started(self):
        """Test that agent_environment property works after client is started."""
        async def init_agent(env: AgentEnvironment):
            pass

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        # Before client(), should raise
        with pytest.raises(ValueError, match="Agent environment has not been set up yet"):
            _ = scenario.agent_environment

        async with scenario.client() as client:
            # After client() starts, should be accessible
            env = scenario.agent_environment
            assert isinstance(env, AgentEnvironment)

    @pytest.mark.asyncio
    async def test_echo_agent_responds_to_message(self):
        """Test an echo agent that responds to messages."""
        async def init_agent(env: AgentEnvironment):
            app = env.agent_application

            async def echo_handler(context: TurnContext, state: TurnState):
                await context.send_activity(f"Echo: {context.activity.text}")

            app.activity(ActivityTypes.message)(echo_handler)

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            responses = await client.send("Hello, Agent!", response_wait=0.1)
            
            # Filter for message activities (ignore typing indicators, etc.)
            message_responses = [r for r in responses if isinstance(r, Activity) and r.type == ActivityTypes.message]
            
            assert len(message_responses) >= 1
            assert "Echo: Hello, Agent!" in message_responses[0].text

    @pytest.mark.asyncio
    async def test_agent_can_send_multiple_responses(self):
        """Test an agent that sends multiple responses to a single message."""
        async def init_agent(env: AgentEnvironment):
            app = env.agent_application

            async def multi_response_handler(context: TurnContext, state: TurnState):
                await context.send_activity("Response 1")
                await context.send_activity("Response 2")

            app.activity(ActivityTypes.message)(multi_response_handler)

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            responses = await client.send("Hello", response_wait=0.2)
            
            message_responses = [r for r in responses if isinstance(r, Activity) and r.type == ActivityTypes.message]
            
            assert len(message_responses) >= 2
            texts = [r.text for r in message_responses]
            assert "Response 1" in texts
            assert "Response 2" in texts

    @pytest.mark.asyncio
    async def test_custom_config_is_used(self):
        """Test that custom AgentScenarioConfig is used."""
        custom_config = AgentScenarioConfig()
        custom_config.response_server_port = 9999

        async def init_agent(env: AgentEnvironment):
            pass

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            config=custom_config,
            use_jwt_middleware=False,
        )

        assert scenario._config is custom_config
        assert scenario._config.response_server_port == 9999

    @pytest.mark.asyncio
    async def test_jwt_middleware_disabled(self):
        """Test that JWT middleware can be disabled."""
        async def init_agent(env: AgentEnvironment):
            pass

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        assert len(scenario._application.middlewares) == 0

    @pytest.mark.asyncio
    async def test_agent_receives_activity_properties(self):
        """Test that the agent receives correct activity properties from the client."""
        received_activity = None

        async def init_agent(env: AgentEnvironment):
            app = env.agent_application

            async def capture_handler(context: TurnContext, state: TurnState):
                nonlocal received_activity
                received_activity = context.activity
                await context.send_activity("Received")

            app.activity(ActivityTypes.message)(capture_handler)

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("Test message", response_wait=0.1)

            assert received_activity is not None
            assert received_activity.text == "Test message"
            assert received_activity.type == ActivityTypes.message

    @pytest.mark.asyncio
    async def test_agent_application_state_persists(self):
        """Test that state configured in init_agent persists throughout the session."""
        async def init_agent(env: AgentEnvironment):
            app = env.agent_application
            app._test_marker = "initialized"

            async def handler(context: TurnContext, state: TurnState):
                await context.send_activity(f"Marker: {app._test_marker}")

            app.activity(ActivityTypes.message)(handler)

        scenario = AiohttpAgentScenario(
            init_agent=init_agent,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            responses = await client.send("Check marker", response_wait=0.1)
            
            message_responses = [r for r in responses if isinstance(r, Activity) and r.type == ActivityTypes.message]
            
            assert any("Marker: initialized" in r.text for r in message_responses)
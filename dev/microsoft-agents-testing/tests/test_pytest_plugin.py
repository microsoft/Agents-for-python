# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Integration tests for the pytest plugin.

These tests verify the pytest plugin fixtures work correctly by using them
with real AiohttpScenario instances. The tests use the @pytest.mark.agent_test
marker and request the fixtures as test parameters, exactly as end users would.
"""

import pytest

from microsoft_agents.hosting.core import TurnContext, TurnState, AgentApplication

from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment


# ============================================================================
# Helper: Create a simple echo agent scenario
# ============================================================================


async def init_echo_agent(env: AgentEnvironment) -> None:
    """Initialize a simple echo agent for testing."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(f"Echo: {context.activity.text}")


# Create a reusable scenario for the plugin tests
echo_scenario = AiohttpScenario(
    init_agent=init_echo_agent,
    use_jwt_middleware=False,
)


# ============================================================================
# agent_client Fixture Tests
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestAgentClientFixture:
    """Tests for the agent_client fixture using a real AiohttpScenario."""

    @pytest.mark.asyncio
    async def test_agent_client_is_provided(self, agent_client):
        """agent_client fixture provides a working client."""
        assert agent_client is not None

    @pytest.mark.asyncio
    async def test_agent_client_can_send_message(self, agent_client):
        """agent_client can send messages and receive responses."""
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Hello!")

    @pytest.mark.asyncio
    async def test_agent_client_has_transcript(self, agent_client):
        """agent_client maintains a transcript of exchanges."""
        await agent_client.send("Test message", wait=0.2)
        
        # Transcript should have at least one exchange
        assert agent_client.transcript is not None

    @pytest.mark.asyncio
    async def test_agent_client_multiple_messages(self, agent_client):
        """agent_client handles multiple messages in sequence."""
        await agent_client.send("First")
        await agent_client.send("Second")
        await agent_client.send("Third", wait=0.2)
        
        agent_client.expect().that_for_any(text="Echo: First")
        agent_client.expect().that_for_any(text="Echo: Second")
        agent_client.expect().that_for_any(text="Echo: Third")


# ============================================================================
# agent_environment Fixture Tests
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestAgentEnvironmentFixture:
    """Tests for the agent_environment fixture."""

    def test_agent_environment_is_provided(self, agent_environment):
        """agent_environment fixture provides the AgentEnvironment."""
        assert agent_environment is not None
        assert isinstance(agent_environment, AgentEnvironment)

    def test_agent_environment_has_config(self, agent_environment):
        """agent_environment provides access to SDK config."""
        assert agent_environment.config is not None
        assert isinstance(agent_environment.config, dict)

    def test_agent_environment_has_agent_application(self, agent_environment):
        """agent_environment provides access to the AgentApplication."""
        assert agent_environment.agent_application is not None

    def test_agent_environment_has_storage(self, agent_environment):
        """agent_environment provides access to storage."""
        assert agent_environment.storage is not None

    def test_agent_environment_has_adapter(self, agent_environment):
        """agent_environment provides access to the adapter."""
        assert agent_environment.adapter is not None

    def test_agent_environment_has_authorization(self, agent_environment):
        """agent_environment provides access to authorization."""
        assert agent_environment.authorization is not None

    def test_agent_environment_has_connections(self, agent_environment):
        """agent_environment provides access to connections."""
        assert agent_environment.connections is not None


# ============================================================================
# Derived Fixtures Tests (agent_application, storage, etc.)
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestDerivedFixtures:
    """Tests for fixtures derived from agent_environment."""

    def test_agent_application_fixture(self, agent_application):
        """agent_application fixture provides the AgentApplication instance."""
        assert agent_application is not None
        assert isinstance(agent_application, AgentApplication)

    def test_authorization_fixture(self, authorization):
        """authorization fixture provides the Authorization instance."""
        assert authorization is not None

    def test_storage_fixture(self, storage):
        """storage fixture provides the Storage instance."""
        assert storage is not None

    def test_adapter_fixture(self, adapter):
        """adapter fixture provides the ChannelServiceAdapter instance."""
        assert adapter is not None

    def test_connection_manager_fixture(self, connection_manager):
        """connection_manager fixture provides the Connections instance."""
        assert connection_manager is not None


# ============================================================================
# Combined Fixtures Tests
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestCombinedFixtures:
    """Tests that use multiple fixtures together."""

    @pytest.mark.asyncio
    async def test_client_and_environment_work_together(
        self, agent_client, agent_environment
    ):
        """agent_client and agent_environment can be used together."""
        # Verify environment is available
        assert agent_environment.agent_application is not None
        
        # Use client to send a message
        await agent_client.send("Hello from combined test!", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Hello from combined test!")

    @pytest.mark.asyncio
    async def test_all_fixtures_available(
        self,
        agent_client,
        agent_environment,
        agent_application,
        authorization,
        storage,
        adapter,
        connection_manager,
    ):
        """All fixtures can be requested together."""
        # All fixtures should be available
        assert agent_client is not None
        assert agent_environment is not None
        assert agent_application is not None
        assert authorization is not None
        assert storage is not None
        assert adapter is not None
        assert connection_manager is not None
        
        # Derived fixtures should match environment components
        assert agent_application is agent_environment.agent_application
        assert authorization is agent_environment.authorization
        assert storage is agent_environment.storage
        assert adapter is agent_environment.adapter
        assert connection_manager is agent_environment.connections


# ============================================================================
# Stateful Agent Tests
# ============================================================================


async def init_counter_agent(env: AgentEnvironment) -> None:
    """Initialize an agent that counts messages using storage."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        # Use state to count messages
        count = (state.conversation.get_value("count") or 0) + 1
        state.conversation.set_value("count", count)
        await context.send_activity(f"Message #{count}")


counter_scenario = AiohttpScenario(
    init_agent=init_counter_agent,
    use_jwt_middleware=False,
)


@pytest.mark.agent_test(counter_scenario)
class TestStatefulAgentWithFixtures:
    """Tests for a stateful agent using fixtures."""

    @pytest.mark.asyncio
    async def test_storage_persists_across_messages(self, agent_client, storage):
        """Storage fixture provides access to the same storage instance used by agent."""
        assert storage is not None
        
        await agent_client.send("one")
        await agent_client.send("two")
        await agent_client.send("three", wait=0.2)
        
        agent_client.expect().that_for_any(text="Message #1")
        agent_client.expect().that_for_any(text="Message #2")
        agent_client.expect().that_for_any(text="Message #3")


# ============================================================================
# Function-Level Marker Tests
# ============================================================================


class TestFunctionLevelMarker:
    """Tests that @pytest.mark.agent_test works on individual functions."""

    @pytest.mark.agent_test(echo_scenario)
    @pytest.mark.asyncio
    async def test_marker_on_function(self, agent_client):
        """@pytest.mark.agent_test works on individual test functions."""
        await agent_client.send("Function-level test", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Function-level test")

    @pytest.mark.agent_test(echo_scenario)
    def test_environment_on_function(self, agent_environment):
        """agent_environment works with function-level marker."""
        assert agent_environment is not None
        assert agent_environment.agent_application is not None


# ============================================================================
# URL String Marker Tests (ExternalScenario)
# ============================================================================


class TestUrlStringMarker:
    """Tests that verify URL string markers create ExternalScenario."""

    def test_url_creates_external_scenario(self):
        """URL string in marker creates an ExternalScenario."""
        from unittest.mock import Mock
        from microsoft_agents.testing.pytest_plugin import _get_scenario_from_marker
        from microsoft_agents.testing.core import ExternalScenario
        
        marker = Mock()
        marker.args = ("http://localhost:3978/api/messages",)
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        result = _get_scenario_from_marker(item)

        assert isinstance(result, ExternalScenario)
        assert result._endpoint == "http://localhost:3978/api/messages"


# ============================================================================
# Marker Validation Tests
# ============================================================================


class TestMarkerValidation:
    """Tests for marker argument validation."""

    def test_marker_requires_argument(self):
        """@pytest.mark.agent_test requires an argument."""
        from unittest.mock import Mock
        from microsoft_agents.testing.pytest_plugin import _get_scenario_from_marker
        
        marker = Mock()
        marker.args = ()
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        with pytest.raises(pytest.UsageError, match="requires an argument"):
            _get_scenario_from_marker(item)

    def test_marker_rejects_invalid_type(self):
        """@pytest.mark.agent_test rejects non-string/non-Scenario arguments."""
        from unittest.mock import Mock
        from microsoft_agents.testing.pytest_plugin import _get_scenario_from_marker
        
        marker = Mock()
        marker.args = (12345,)
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        with pytest.raises(pytest.UsageError, match="expects a URL string or Scenario"):
            _get_scenario_from_marker(item)

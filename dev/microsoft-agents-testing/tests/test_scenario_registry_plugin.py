# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Tests for the scenario registry integration with the pytest plugin.

These tests verify that _get_scenario_from_marker correctly resolves
registered scenario names from the global scenario_registry, and that
URL strings and direct Scenario instances still work as expected.
"""

import pytest
from unittest.mock import Mock

from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment
from microsoft_agents.testing.pytest_plugin import _get_scenario_from_marker
from microsoft_agents.testing.core import ExternalScenario
from microsoft_agents.testing import scenario_registry


# ============================================================================
# Helpers: Define scenarios in this module (separate from test_pytest_plugin)
# ============================================================================


async def init_echo_agent(env: AgentEnvironment) -> None:
    """Initialize a simple echo agent for testing."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(f"Echo: {context.activity.text}")


_echo_scenario = AiohttpScenario(
    init_agent=init_echo_agent,
    use_jwt_middleware=False,
)


# ============================================================================
# Unit Tests: _get_scenario_from_marker with the registry
# ============================================================================


class TestRegisteredScenarioFlow:
    """Tests for using registered scenarios with @pytest.mark.agent_test.

    When a non-URL string is passed to the marker, it should look up
    the scenario by name in the global scenario_registry.
    """

    def test_registered_name_resolves_to_scenario(self):
        """A registered scenario name resolves via _get_scenario_from_marker."""
        scenario_registry.register(
            "test.registry.echo",
            _echo_scenario,
            description="Echo for registry tests",
        )
        try:
            marker = Mock()
            marker.args = ("test.registry.echo",)
            item = Mock()
            item.get_closest_marker = Mock(return_value=marker)

            result = _get_scenario_from_marker(item)

            assert result is _echo_scenario
        finally:
            scenario_registry.clear()

    def test_unregistered_name_raises_key_error(self):
        """An unregistered scenario name raises KeyError."""
        scenario_registry.clear()

        marker = Mock()
        marker.args = ("nonexistent.scenario",)
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        with pytest.raises(KeyError, match="nonexistent.scenario"):
            _get_scenario_from_marker(item)

    def test_url_string_still_creates_external_scenario(self):
        """URL strings still create ExternalScenario (not registry lookup)."""
        marker = Mock()
        marker.args = ("https://my-agent.azurewebsites.net/api/messages",)
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        result = _get_scenario_from_marker(item)

        assert isinstance(result, ExternalScenario)

    def test_registered_scenario_object_passthrough(self):
        """Passing a Scenario instance directly still works alongside registry."""
        marker = Mock()
        marker.args = (_echo_scenario,)
        item = Mock()
        item.get_closest_marker = Mock(return_value=marker)

        result = _get_scenario_from_marker(item)

        assert result is _echo_scenario

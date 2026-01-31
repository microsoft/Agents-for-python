# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# """
# Pytest plugin for Microsoft Agents Testing framework.

# This plugin provides:
# - @pytest.mark.agent_test marker for decorating test classes/functions
# - Automatic fixtures: agent_client, conv, agent_environment, etc.

# Usage:
#     @pytest.mark.agent_test("http://localhost:3978/api/messages")
#     class TestMyAgent:
#         async def test_hello(self, conv):
#             response = await conv.send("hello")
#             response.check.text.contains("Hello")

#     # Or with a custom scenario:
#     @pytest.mark.agent_test(my_scenario)
#     async def test_something(conv):
#         ...
# """

# from __future__ import annotations

# from typing import cast

# import pytest

# from microsoft_agents.hosting.core import (
#     AgentApplication,
#     Authorization,
#     ChannelServiceAdapter,
#     Connections,
#     Storage,
# )

# from .client import AgentClient, ConversationClient
# from .scenario import ExternalScenario, Scenario, AgentEnvironment


# # Store the scenario per test item
# _SCENARIO_KEY = "_agent_test_scenario"


# def pytest_configure(config: pytest.Config) -> None:
#     """Register the agent_test marker."""
#     config.addinivalue_line(
#         "markers",
#         "agent_test(scenario): mark test to use agent testing fixtures. "
#         "Pass a URL string or a Scenario instance.",
#     )


# def _get_scenario_from_marker(item: pytest.Item) -> Scenario | None:
#     """Extract scenario from the agent_test marker on a test item."""
#     marker = item.get_closest_marker("agent_test")
#     if marker is None:
#         return None

#     if not marker.args:
#         raise pytest.UsageError(
#             f"@pytest.mark.agent_test requires an argument (URL string or Scenario). "
#             f"Example: @pytest.mark.agent_test('http://localhost:3978/api/messages')"
#         )

#     arg = marker.args[0]
#     if isinstance(arg, str):
#         return ExternalScenario(arg)
#     elif isinstance(arg, Scenario):
#         return arg
#     else:
#         raise pytest.UsageError(
#             f"@pytest.mark.agent_test expects a URL string or Scenario instance, "
#             f"got {type(arg).__name__}"
#         )


# @pytest.hookimpl(tryfirst=True)
# def pytest_runtest_setup(item: pytest.Item) -> None:
#     """Store the scenario on the test item before test setup."""
#     scenario = _get_scenario_from_marker(item)
#     if scenario is not None:
#         setattr(item, _SCENARIO_KEY, scenario)


# # =============================================================================
# # Fixtures
# # =============================================================================


# @pytest.fixture
# async def agent_client(request: pytest.FixtureRequest):
#     """
#     Provides an AgentClient for communicating with the agent under test.
    
#     Only available when the test is decorated with @pytest.mark.agent_test.
#     """
#     scenario: Scenario | None = getattr(request.node, _SCENARIO_KEY, None)
    
#     if scenario is None:
#         pytest.skip("agent_client fixture requires @pytest.mark.agent_test marker")
#         return
    
#     async with scenario.client() as client:
#         yield client
#         # After test completes, attach conversation to the test item
#         # This makes it available to pytest's reporting hooks
#         request.node._agent_client_transcript = client.transcript


# @pytest.fixture
# def conv(agent_client: AgentClient) -> ConversationClient:
#     """
#     Provides a ConversationClient for high-level agent interaction.
    
#     Only available when the test is decorated with @pytest.mark.agent_test.
#     """
#     return ConversationClient(agent_client)


# @pytest.fixture
# def agent_environment(request: pytest.FixtureRequest) -> AgentEnvironment:
#     """
#     Provides access to the AgentEnvironment (only for in-process scenarios).
    
#     Only available when using AiohttpScenario or similar in-process scenarios.
#     """
#     scenario: Scenario | None = getattr(request.node, _SCENARIO_KEY, None)
    
#     if scenario is None:
#         pytest.skip("agent_environment fixture requires @pytest.mark.agent_test marker")
    
#     if not hasattr(scenario, "agent_environment"):
#         pytest.skip(
#             "agent_environment fixture is only available for in-process scenarios "
#             "(e.g., AiohttpScenario), not for ExternalScenario"
#         )
    
#     return cast(AgentEnvironment, scenario.agent_environment)


# @pytest.fixture
# def agent_application(agent_environment: AgentEnvironment) -> AgentApplication:
#     """Provides the AgentApplication instance from the test scenario."""
#     return agent_environment.agent_application


# @pytest.fixture
# def authorization(agent_environment: AgentEnvironment) -> Authorization:
#     """Provides the Authorization instance from the test scenario."""
#     return agent_environment.authorization


# @pytest.fixture
# def storage(agent_environment: AgentEnvironment) -> Storage:
#     """Provides the Storage instance from the test scenario."""
#     return agent_environment.storage


# @pytest.fixture
# def adapter(agent_environment: AgentEnvironment) -> ChannelServiceAdapter:
#     """Provides the ChannelServiceAdapter instance from the test scenario."""
#     return agent_environment.adapter


# @pytest.fixture
# def connection_manager(agent_environment: AgentEnvironment) -> Connections:
#     """Provides the Connections (connection manager) instance from the test scenario."""
#     return agent_environment.connections
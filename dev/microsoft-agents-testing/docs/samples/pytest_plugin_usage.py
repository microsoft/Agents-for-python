#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Pytest Plugin — use @pytest.mark.agent_test for zero-boilerplate tests.

Features demonstrated:
  - @pytest.mark.agent_test(scenario) — class-level and function-level markers.
  - agent_client fixture              — sends messages, collects replies.
  - agent_environment fixture         — inspect the agent's internals.
  - Derived fixtures                  — agent_application, storage, adapter,
                                        authorization, connection_manager.
  - Registered scenario names         — pass a string name instead of an object.
  - Expect / Select via client        — fluent assertions right on the client.

Run::

    pytest docs/samples/pytest_plugin_usage.py -v

Note: requires the pytest plugin to be installed (it is auto-discovered
via the ``microsoft_agents.testing`` entry point).
"""

import pytest

from microsoft_agents.hosting.core import TurnContext, TurnState, AgentApplication
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    scenario_registry,
)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

async def init_echo(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState):
        await ctx.send_activity(f"Echo: {ctx.activity.text}")


echo_scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)


# ---------------------------------------------------------------------------
# 1) Class-level marker — every test in the class gets the same scenario
# ---------------------------------------------------------------------------

@pytest.mark.agent_test(echo_scenario)
class TestClassLevelMarker:
    """All tests share the echo_scenario."""

    @pytest.mark.asyncio
    async def test_send_and_receive(self, agent_client):
        """agent_client is automatically provided by the plugin."""
        await agent_client.send_expect_replies("Hi!")
        agent_client.expect().that_for_any(text="Echo: Hi!")

    def test_environment_access(self, agent_environment):
        """agent_environment exposes the in-process agent components."""
        assert isinstance(agent_environment, AgentEnvironment)
        assert agent_environment.agent_application is not None

    def test_derived_fixtures(self, agent_application, storage, adapter):
        """Derived fixtures provide typed access to individual components."""
        assert isinstance(agent_application, AgentApplication)
        assert storage is not None
        assert adapter is not None


# ---------------------------------------------------------------------------
# 2) Function-level marker — different scenarios per test
# ---------------------------------------------------------------------------

class TestFunctionLevelMarker:

    @pytest.mark.agent_test(echo_scenario)
    @pytest.mark.asyncio
    async def test_echo(self, agent_client):
        await agent_client.send_expect_replies("Hello")
        agent_client.expect().that_for_any(text="Echo: Hello")


# ---------------------------------------------------------------------------
# 3) Registered scenario name — look up by string
# ---------------------------------------------------------------------------

# Register the scenario so it can be referenced by name
scenario_registry.register(
    "samples.pytest.echo",
    echo_scenario,
    description="Echo agent for pytest plugin sample",
)


@pytest.mark.agent_test("samples.pytest.echo")
class TestRegisteredName:
    """Pass a registered name instead of the scenario object."""

    @pytest.mark.asyncio
    async def test_via_registry(self, agent_client):
        await agent_client.send_expect_replies("Registry!")
        agent_client.expect().that_for_any(text="Echo: Registry!")


# ---------------------------------------------------------------------------
# 4) Using Select and Expect through the client
# ---------------------------------------------------------------------------

@pytest.mark.agent_test(echo_scenario)
class TestFluentAssertionsThroughClient:

    @pytest.mark.asyncio
    async def test_expect_shortcuts(self, agent_client):
        """client.expect() and client.select() shortcut methods."""
        await agent_client.send_expect_replies("AAA")
        await agent_client.send_expect_replies("BBB")

        # expect(history=True) asserts over all responses so far
        agent_client.expect(history=True).that_for_any(text="Echo: AAA")
        agent_client.expect(history=True).that_for_any(text="Echo: BBB")

        # select(history=True) lets you filter first
        msgs = agent_client.select(history=True).where(type="message").get()
        assert len(msgs) >= 2

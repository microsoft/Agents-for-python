# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Basic echo scenario for testing simple agent interactions."""

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from microsoft_agents.testing.aiohttp_scenario import (
    AiohttpScenario,
    AgentEnvironment,
)

async def basic_scenario_init(env: AgentEnvironment):
    """Initialize the basic echo agent.

    Registers a single message handler that echoes back whatever
    the user sends, prefixed with "Echo: ".

    :param env: The AgentEnvironment for configuring the agent.
    """

    app: AgentApplication[TurnState] = env.agent_application

    @app.activity(ActivityTypes.message)
    async def handler(context: TurnContext, state: TurnState):
        """Echo handler: replies with the user's message."""
        await context.send_activity("Echo: " + context.activity.text)

# Pre-built scenario instances for CLI registration
basic_scenario = AiohttpScenario(basic_scenario_init)
basic_scenario_no_auth = AiohttpScenario(basic_scenario_init, use_jwt_middleware=False)
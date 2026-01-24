from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from microsoft_agents.testing.agent_scenario import (
    AiohttpAgentScenario,
    AgentEnvironment,
)

async def init_agent(env: AgentEnvironment):

    """Initialize the application for the basic sample."""

    app: AgentApplication[TurnState] = env.agent_application

    @app.activity(ActivityTypes.message)
    async def handler(context: TurnContext, state: TurnState):
        await context.send_activity("Echo: " + context.activity.text)

basic_scenario = AiohttpAgentScenario(init_agent)
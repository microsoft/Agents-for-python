import click

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from microsoft_agents.testing.agent_scenario import (
    AgentScenarioConfig,
    AiohttpAgentScenario,
    AgentEnvironment,
)


def create_auth_route(auth_handler_id: str, agent: AgentApplication):
    """Create a dynamic function to handle authentication routes."""

    async def dynamic_function(context: TurnContext, state: TurnState):
        token = await agent.auth.get_token(context, auth_handler_id)
        await context.send_activity(f"Hello from {auth_handler_id}! Token: {token}")

    dynamic_function.__name__ = f"auth_route_{auth_handler_id}".lower()
    click.echo(f"Creating route: {dynamic_function.__name__} for handler {auth_handler_id}")
    return dynamic_function

async def init_agent(env: AgentEnvironment):

    """Initialize the application for the auth sample."""

    app: AgentApplication[TurnState] = env.agent_application

    assert app._auth
    assert app._auth._handlers

    for authorization_handler in app._auth._handlers.values():
        auth_handler = authorization_handler._handler
        app.message(
            auth_handler.name.lower(),
            auth_handlers=[auth_handler.name],
        )(create_auth_route(auth_handler.name, app))

    async def handle_message(context: TurnContext, state: TurnState):
        await context.send_activity("Hello from the auth testing sample! Enter the name of an auth handler to test it.")

    app.activity(ActivityTypes.message)(handle_message)

auth_scenario = AiohttpAgentScenario(init_agent)
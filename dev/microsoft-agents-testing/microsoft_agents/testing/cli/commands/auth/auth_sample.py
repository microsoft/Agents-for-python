import os
import click

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from microsoft_agents.testing.integration import Sample


def create_auth_route(auth_handler_id: str, agent: AgentApplication):
    """Create a dynamic function to handle authentication routes."""

    async def dynamic_function(context: TurnContext, state: TurnState):
        token = await agent.auth.get_token(context, auth_handler_id)
        await context.send_activity(f"Hello from {auth_handler_id}! Token: {token}")

    dynamic_function.__name__ = f"auth_route_{auth_handler_id}".lower()
    click.echo(f"Creating route: {dynamic_function.__name__} for handler {auth_handler_id}")
    return dynamic_function


class AuthSample(Sample):
    """A quickstart sample implementation."""

    @classmethod
    async def get_config(cls) -> dict:
        """Retrieve the configuration for the sample."""
        return dict(os.environ)
    
    async def init_app(self):
        """Initialize the application for the quickstart sample."""

        app: AgentApplication[TurnState] = self.env.agent_application

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
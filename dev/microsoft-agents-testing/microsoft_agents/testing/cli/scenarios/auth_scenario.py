# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Authentication testing scenario.

Provides a scenario for testing OAuth/authentication flows with agents.
"""

import jwt
import click

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from microsoft_agents.testing.aiohttp_scenario import (
    AgentEnvironment,
    AiohttpScenario,
)

def create_auth_route(auth_handler_id: str, agent: AgentApplication):
    """Create a dynamic function to handle authentication routes."""

    async def dynamic_function(context: TurnContext, state: TurnState):
        token_response = await agent.auth.get_token(context, auth_handler_id)
        try:
            decoded_token = jwt.decode(token_response.token, options={"verify_signature": False})
        except Exception as e:
            decoded_token = f"Error decoding token: {e}"
        await context.send_activity(f"Hello from {auth_handler_id}! Token: {token_response}\n\nDecoded: {decoded_token}")

    dynamic_function.__name__ = f"auth_route_{auth_handler_id}".lower()
    click.echo(f"Creating route: {dynamic_function.__name__} for handler {auth_handler_id}")
    return dynamic_function

def sign_out_route(auth_handler_id: str, agent: AgentApplication):
    """Create a dynamic function to handle sign-out routes."""

    async def dynamic_function(context: TurnContext, state: TurnState):
        await agent.auth.sign_out(context, auth_handler_id)
        await context.send_activity(f"You have been signed out from {auth_handler_id}.")

    dynamic_function.__name__ = f"sign_out_route_{auth_handler_id}".lower()
    click.echo(f"Creating sign-out route: {dynamic_function.__name__} for handler {auth_handler_id}")
    return dynamic_function

async def auth_scenario_init(env: AgentEnvironment):

    """Initialize the application for the auth sample."""

    app: AgentApplication[TurnState] = env.agent_application

    auth = env.authorization

    if auth._handlers:

        click.echo("To test authentication flows, send a message with the name of the auth handler (all lowercase) you want to test. For example, if you have a handler named 'Graph', send 'Graph' to test it.")
        click.echo("To sign out, send '/signout {handlername}'. For example, '/signout Graph' to sign out of the Graph handler.")
        click.echo("\n")

        for authorization_handler in auth._handlers.values():
            auth_handler = authorization_handler._handler
            app.message(
                auth_handler.name.lower(),
                auth_handlers=[auth_handler.name],
            )(create_auth_route(auth_handler.name, app))
            app.message(f"/signout {auth_handler.name.lower()}")(sign_out_route(auth_handler.name, app))
    else:
        click.echo("No auth handlers found in the agent application. Please add auth handlers to test authentication flows.")

    async def handle_message(context: TurnContext, state: TurnState):
        await context.send_activity("Hello from the auth testing sample! Enter the name of an auth handler to test it.")

    app.activity(ActivityTypes.message)(handle_message)

auth_scenario = AiohttpScenario(auth_scenario_init)
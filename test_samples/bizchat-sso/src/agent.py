# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from os import environ
from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import (
    MsalConnectionManager,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    AuthHandlerSettings,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.testing.pytest_plugin import adapter

from start_server import start_server

logging.basicConfig(level=logging.INFO)
load_dotenv(".env")

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)

AUTHORIZATION = Authorization(
    STORAGE,
    CONNECTION_MANAGER,
    auth_handlers={
        "SSO": AuthHandlerSettings(
            name="SSO",
            title="Sign in to the Agent",
            text="Please sign in to continue",
            abs_oauth_connection_name="sso",
        )
    },
    **agents_sdk_config,
)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, authorization=AUTHORIZATION, **agents_sdk_config
)


async def _help(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the Echo Agent sample 🚀. "
        "Type /help for help or send a message to see the echo feature in action."
    )


AGENT_APP.conversation_update("membersAdded")(_help)

AGENT_APP.message("/help")(_help)


@AGENT_APP.message("/auth", auth_handlers=["SSO"])
async def auth_message(context: TurnContext, _):
    await context.send_activity("You are authenticated! 🎉")


@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    await AGENT_APP.auth.sign_out(context, "SSO")
    await context.send_activity("You have been logged out.")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _):
    await context.send_activity(f"you said: {context.activity.text}")


if __name__ == "__main__":
    try:
        start_server(
            agent_application=AGENT_APP,
            adapter=ADAPTER,
            auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
        )
    except Exception as error:
        raise error

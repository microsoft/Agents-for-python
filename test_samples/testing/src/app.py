# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""An AgentApplication that can run through aiohttp or an in-memory test adapter."""

from os import environ

from dotenv import load_dotenv

from microsoft_agents.activity import ActivityTypes, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.core import (
    AgentApplication,
    ApplicationOptions,
    MemoryStorage,
    TurnContext,
    TurnState,
)

load_dotenv()

CONFIGURATION = load_configuration_from_env(environ)
CONNECTION_MANAGER = MsalConnectionManager(**CONFIGURATION)
AGENT_APP = AgentApplication[TurnState](
    options=ApplicationOptions(
        storage=MemoryStorage(),
        start_typing_timer=False,
    ),
    connection_manager=CONNECTION_MANAGER,
)


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity("Welcome! Send a message and I will echo it back.")


@AGENT_APP.message("/help")
async def help_command(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity("Send any message to receive an echo response.")


@AGENT_APP.activity(ActivityTypes.message)
async def echo_message(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(f"Echo: {context.activity.text}")


if __name__ == "__main__":
    from microsoft_agents.hosting.aiohttp import CloudAdapter

    from start_server import start_server

    cloud_adapter = CloudAdapter(connection_manager=CONNECTION_MANAGER)
    start_server(
        AGENT_APP,
        cloud_adapter,
        CONNECTION_MANAGER.get_default_connection_configuration(),
    )

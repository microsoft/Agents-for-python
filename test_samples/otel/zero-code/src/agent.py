# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import re
import sys
import traceback
from os import environ

from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)

from .card import create_profile_card
from .get_user_info import get_user_info

load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the empty agent! "
        "This agent is designed to be a starting point for your own agent development."
    )

@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    await AGENT_APP.auth.sign_out(context, "GRAPH")
    await context.send_activity(MessageFactory.text("You have been logged out."))


@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")
    if user_token_response is not None:
        user_info = await get_user_info(user_token_response.token)
        activity = MessageFactory.attachment(create_profile_card(user_info))
        await context.send_activity(activity)
    else:
        await context.send_activity('Token not available. Enter "login" to sign in.')


@AGENT_APP.message(re.compile(r"^hello$"))
async def on_hello(context: TurnContext, _state: TurnState):
    await asyncio.sleep(5)  # Simulate some processing delay
    await context.send_activity("Hello!")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(f"you said: {context.activity.text}")


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("The bot encountered an error or bug.")

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
from os import environ, path
from dotenv import load_dotenv

from microsoft.agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
    MemoryStorage,
)
from microsoft.agents.activity import load_configuration_from_env
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.authentication.msal import MsalConnectionManager

# Load configuration from environment
load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, state: TurnState):
    """
    Internal method to check authorization status for all configured handlers.
    Returns True if at least one handler has a valid token.
    """
    await context.send_activity("Welcome to the OBO Auth App demo! Use **obo** to login and trigger OBO token exchange or enter **status** to check authorization status.")

@AGENT_APP.message("obo", auth_handlers=["GRAPH"])
async def obo(context: TurnContext, state: TurnState):
    tresp = await AGENT_APP.auth.get_token(context, "GRAPH")
    if tresp and tresp.token:
        await context.send_activity(
            MessageFactory.text(f"Graph token: {tresp.token[:10]}... (truncated)")
        )
    else:
        await context.send_activity(
            MessageFactory.text(f"Token request status: {tresp or 'unknown'}")
        )
    obo_token = await AGENT_APP.auth.exchange_token(
        context, ["https://graph.microsoft.com/.default"], "GRAPH"
    )
    await context.send_activity(
        MessageFactory.text(
            f"OBO Token received: {len(obo_token.token) if obo_token and obo_token.token else 0} characters"
        )
    )

@AGENT_APP.message(re.compile(r"^(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState):
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return False

    try:
        # Check status for each auth handlerF
        status_messages = []
        has_valid_token = False

        for handler_id in AGENT_APP.auth._auth_handlers.keys():
            try:
                token_response = await AGENT_APP.auth.get_token(context, handler_id)
                if token_response and token_response.token:
                    status_messages.append(f"✅ {handler_id}: Connected")
                    has_valid_token = True
                else:
                    status_messages.append(f"❌ {handler_id}: Not connected")
            except Exception as e:
                status_messages.append(f"❌ {handler_id}: Error - {str(e)}")

        status_text = "Authorization Status:\n" + "\n".join(status_messages)
        await context.send_activity(MessageFactory.text(status_text))
        return has_valid_token

    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error checking status: {str(e)}")
        )
        return False

@AGENT_APP.message(re.compile(r"^(logout|signout|sign out)", re.IGNORECASE))
async def logout(context: TurnContext, state: TurnState) -> None:
    """
    Handler for logout requests.
    Clears the tokens for both Graph and GitHub.
    """
    await AGENT_APP.auth.sign_out(context, state)
    await context.send_activity(MessageFactory.text("User logged out."))


@AGENT_APP.on_sign_in_success
async def sign_in_success(context: TurnContext, state: TurnState, _auth_handler_id: str) -> None:
    """
    Handler for successful sign-in events.
    """
    await context.send_activity(
        MessageFactory.text("Sign-in successful! You can now use the bot's features.")
    )

@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

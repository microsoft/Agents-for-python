# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
import logging, json
from os import environ, path
from dotenv import load_dotenv

from microsoft.agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
    CardFactory,
    MemoryStorage,
)
from microsoft.agents.activity import load_configuration_from_env, ActivityTypes
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.authentication.msal import MsalConnectionManager

from .github_api_client import get_current_profile, get_pull_requests
from .user_graph_client import get_user_info
from .cards import create_profile_card, create_pr_card

logger = logging.getLogger(__name__)

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


@AGENT_APP.message(re.compile(r"^(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState) -> bool:
    """
    Internal method to check authorization status for all configured handlers.
    Returns True if at least one handler has a valid token.
    """
    await context.send_activity(MessageFactory.text("Welcome to the auto-signin demo"))
    tok_graph = await AGENT_APP.auth.get_token(context, GRAPH)
    tok_github = await AGENT_APP.auth.get_token(context, GITHUB)
    status_graph = tok_graph.token is not None
    status_github = tok_github.token is not None
    await context.send_activity(
        MessageFactory.text(
            f"Graph status: {'Connected' if status_graph else 'Not connected'}\n"
            f"GitHub status: {'Connected' if status_github else 'Not connected'}"
        )
    )


@AGENT_APP.message(re.compile(r"^(logout|signout|sign out)", re.IGNORECASE))
async def logout(context: TurnContext, state: TurnState) -> None:
    """
    Handler for logout requests.
    Clears the tokens for both Graph and GitHub.
    """
    await AGENT_APP.auth.sign_out(context, state)
    await context.send_activity(MessageFactory.text("User logged out."))


@AGENT_APP.on_sign_in_success
async def sign_in_success(context: TurnContext, state: TurnState) -> None:
    """
    Handler for successful sign-in events.
    """
    await context.send_activity(
        MessageFactory.text("Sign-in successful! You can now use the bot's features.")
    )


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

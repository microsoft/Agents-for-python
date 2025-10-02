# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
from dotenv import load_dotenv
from typing import cast, Any

from azure.core.credentials import AccessToken, TokenCredential
from msgraph.graph_service_client import GraphServiceClient

from os import environ
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    AgenticUserAuthorization,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

load_dotenv()  # robrandao: todo
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

# robrandao: downloader?
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.activity("message", auth_handlers=["AGENTIC"])
async def on_message(context: TurnContext, _state: TurnState):
    # breakpoint()
    handler = AGENT_APP.auth._resolve_handler("AGENTIC")
    aau_token = await cast(AgenticUserAuthorization, handler).get_agentic_user_token(
        # context, scopes=["https://canary.graph.microsoft.com/.default"]
        context,
        scopes=["User.Read"],
    )
    breakpoint()

    # get_token(context, "AGENTIC")
    upn = context.activity.get_agentic_user()
    assert upn

    # Create GraphServiceClient using the aau_token
    class AgenticTokenCredential(TokenCredential):
        def __init__(self, token: str):
            self.token = token

        def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
            # Return an AccessToken object
            import time

            return AccessToken(token=self.token, expires_on=int(time.time()) + 3600)

    credentials = AgenticTokenCredential(aau_token.token)
    client = GraphServiceClient(credentials=credentials)
    client.request_adapter.base_url = "https://canary.graph.microsoft.com/v1.0"

    try:
        # Get user information
        user = await client.me.get()

        # For now, let's just get user info and demonstrate the token is working
        # You can extend this later with proper Graph API calls for files
        user_name = (
            user.display_name if user and hasattr(user, "display_name") else "User"
        )
        user_email = user.mail if user and hasattr(user, "mail") else "No email"

        response_text = f"Hello {user_name}! Your email is {user_email}. The Graph API is working with your agentic user token!"
        breakpoint()

    except Exception as e:
        response_text = f"Error accessing Microsoft Graph: {str(e)}"

    await context.send_activity(response_text)


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")

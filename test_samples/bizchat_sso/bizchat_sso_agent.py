# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
BizChat SSO reproduction sample for issue #294.

Demonstrates the SSO consent flow in M365 BizChat (Microsoft 365 Chat).
When admin consent has NOT been granted for the OAuth connection, the
token exchange endpoint returns HTTP 400 and the SDK must handle it
gracefully by presenting a sign-in card instead of raising an exception.

To reproduce the bug: run without granting admin consent for the OAuth
connection and send any message in BizChat.
"""

from os import environ, path
import re
import sys
import traceback

from dotenv import load_dotenv
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory,
    MemoryStorage,
)
from microsoft_agents.activity import load_configuration_from_env, ActivityTypes
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from aiohttp.web import Application, Request, Response, run_app

import aiohttp

load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


async def _get_graph_profile(token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            text = await resp.text()
            raise Exception(f"Graph API error {resp.status}: {text}")


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        MessageFactory.text(
            "Welcome to the BizChat SSO sample (issue #294 repro)!\n\n"
            "Commands:\n"
            "- **profile** – sign in via SSO and show your Graph profile\n"
            "- **logout** – sign out\n\n"
            "To reproduce the bug, run this sample WITHOUT granting admin consent "
            "for the OAuth connection and type 'profile' in BizChat."
        )
    )


@AGENT_APP.message(re.compile(r"^(logout|signout|sign out)$", re.IGNORECASE))
async def sign_out(context: TurnContext, state: TurnState):
    await AGENT_APP.auth.sign_out(context, state)
    await context.send_activity(MessageFactory.text("You have been signed out."))


@AGENT_APP.message(re.compile(r"^(profile|me|whoami)$", re.IGNORECASE), auth_handlers=["GRAPH"])
async def get_profile(context: TurnContext, state: TurnState):
    token_response = await AGENT_APP.auth.exchange_token(
        context, scopes=["User.Read"], auth_handler_id="GRAPH"
    )
    if not token_response or not token_response.token:
        await context.send_activity(
            MessageFactory.text("Could not obtain a token. Please sign in first.")
        )
        return

    profile = await _get_graph_profile(token_response.token)
    await context.send_activity(
        MessageFactory.text(
            f"Signed in as: **{profile.get('displayName', 'Unknown')}**\n"
            f"Email: {profile.get('mail') or profile.get('userPrincipalName', 'Unknown')}\n"
            f"ID: {profile.get('id', 'Unknown')}"
        )
    )


@AGENT_APP.activity(ActivityTypes.invoke)
async def on_invoke(context: TurnContext, state: TurnState):
    """
    Handles signin/tokenExchange and signin/verifyState invokes from the channel.

    BizChat (M365) sends signin/tokenExchange when SSO is attempted.
    If admin consent has NOT been granted, the token exchange endpoint returns
    HTTP 400 – this is where issue #294 manifests as an unhandled exception.
    """
    await AGENT_APP.auth.begin_or_continue_flow(context, state)


@AGENT_APP.on_sign_in_success
async def handle_sign_in_success(context: TurnContext, state: TurnState, handler_id: str = None):
    await context.send_activity(
        MessageFactory.text(
            f"Sign-in successful (handler: {handler_id or 'default'}). "
            "Type 'profile' to see your Graph profile."
        )
    )


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(
        MessageFactory.text(
            f"Received: '{context.activity.text}'\n\n"
            "Type **profile** to trigger the SSO flow, or **logout** to sign out."
        )
    )


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n[on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity(
        MessageFactory.text(
            f"An error occurred: {type(error).__name__}: {error}\n\n"
            "If this is a 400 Bad Request from the token exchange endpoint, "
            "you have reproduced issue #294."
        )
    )


async def entry_point(req: Request) -> Response:
    return await start_agent_process(req, AGENT_APP, ADAPTER)


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", entry_point)
APP.router.add_get("/api/messages", lambda _: Response(status=200))
APP["agent_configuration"] = CONNECTION_MANAGER.get_default_connection_configuration()
APP["agent_app"] = AGENT_APP
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        port = int(environ.get("PORT", 3978))
        print(f"BizChat SSO agent listening on http://localhost:{port}/api/messages")
        run_app(APP, host="localhost", port=port)
    except Exception as error:
        raise error

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

from shared import GraphClient, GitHubClient, start_server

load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(config=agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, config=agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](storage=STORAGE, authorization=AUTHORIZATION)
AUTH_HANDLER_IDS = ("GRAPH", "GITHUB", "MCS")


@AGENT_APP.message(re.compile(r"^(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState):
    """Report token availability without starting a sign-in flow."""
    status_messages = []
    has_valid_token = False
    for handler_id in AUTH_HANDLER_IDS:
        token_response = await AGENT_APP.auth.get_token(context, handler_id)
        connected = bool(token_response and token_response.token)
        has_valid_token = has_valid_token or connected
        status_messages.append(
            f"{handler_id}: {'Connected' if connected else 'Not connected'}"
        )

    await context.send_activity(
        MessageFactory.text("Authorization Status:\n" + "\n".join(status_messages))
    )


@AGENT_APP.message("login", auth_handlers=["GRAPH", "GITHUB"])
async def login(context: TurnContext, state: TurnState) -> None:
    await context.send_activity("You are signed in to Graph and GitHub.")


@AGENT_APP.message(re.compile(r"^(logout|signout|sign out)", re.IGNORECASE))
async def sign_out(
    context: TurnContext, state: TurnState, handler_id: str | None = None
):
    """Sign out from the requested handler or all three configured services."""
    for selected_id in (handler_id,) if handler_id else AUTH_HANDLER_IDS:
        await AGENT_APP.auth.sign_out(context, selected_id)
    await context.send_activity(
        MessageFactory.text(
            f"Successfully signed out from {handler_id or 'all services'}."
        )
    )


@AGENT_APP.message(
    re.compile(r"^(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState):
    token_response = await AGENT_APP.auth.exchange_token(
        context, scopes=["User.Read", "email"], auth_handler_id="GRAPH"
    )
    if not token_response or not token_response.token:
        await context.send_activity(
            "Graph token not available. Send 'profile' to sign in again."
        )
        return

    profile_info = await GraphClient.get_me(token_response.token)
    profile_text = (
        f"Profile Information:\n"
        f"Name: {profile_info['displayName']}\n"
        f"Email: {profile_info['mail']}\n"
        f"ID: {profile_info['id']}"
    )
    await context.send_activity(MessageFactory.text(profile_text))


@AGENT_APP.message(
    re.compile(r"^(github profile|gh profile)$", re.IGNORECASE),
    auth_handlers=["GITHUB"],
)
async def profile_github(context: TurnContext, state: TurnState):
    token_response = await AGENT_APP.auth.get_token(context, "GITHUB")
    if not token_response or not token_response.token:
        await context.send_activity(
            "GitHub token not available. Send 'github profile' to sign in again."
        )
        return

    profile_info = await GitHubClient.get_current_profile(token_response.token)
    profile_text = (
        f"GitHub Profile Information:\n"
        f"Name: {profile_info['displayName']}\n"
        f"Email: {profile_info['mail']}\n"
        f"Username: {profile_info['givenName']}\n"
    )
    await context.send_activity(MessageFactory.text(profile_text))
    return


@AGENT_APP.message(
    re.compile(r"^(prs|pull requests)$", re.IGNORECASE), auth_handlers=["GITHUB"]
)
async def pull_requests(context: TurnContext, state: TurnState) -> None:
    token_response = await AGENT_APP.auth.get_token(context, "GITHUB")
    if not token_response or not token_response.token:
        await context.send_activity(
            "GitHub token not available. Send 'prs' to sign in again."
        )
        return

    prs = await GitHubClient.get_pull_requests(
        "octocat", "Hello-World", token_response.token
    )
    pr_text = (
        "Pull Requests:\n" + "\n".join(f"{pr.title}: {pr.url}" for pr in prs)
        if prs
        else "No open pull requests found."
    )
    await context.send_activity(MessageFactory.text(pr_text))


@AGENT_APP.message(
    re.compile(r"^(all profiles|all)", re.IGNORECASE), auth_handlers=["GRAPH", "GITHUB"]
)
async def all_profiles(context: TurnContext, state: TurnState) -> None:
    await profile_request(context, state)
    await profile_github(context, state)


@AGENT_APP.on_sign_in_success
async def handle_sign_in_success(
    context: TurnContext, state: TurnState, handler_id: str | None = None
) -> None:
    """
    Internal method to handle successful sign-in events.
    """
    await context.send_activity(
        MessageFactory.text(
            f"Successfully signed in to {handler_id or 'service'}. You can now use authorized features."
        )
    )


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the Authorization Agent! "
        "You can use commands like 'login', 'status', 'profile', 'prs', or 'logout'. "
        "For OAuth flows, enter the 6-digit verification code when prompted."
    )
    return True


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    await context.send_activity("The bot encountered an error or bug.")


if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        adapter=ADAPTER,
        config=agents_sdk_config,
    )

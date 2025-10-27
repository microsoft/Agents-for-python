# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from os import environ, path
import re
import sys
import traceback

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory,
    MemoryStorage,
)
from microsoft_agents.activity import load_configuration_from_env, ActivityTypes
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    start_agent_process,
    JwtAuthorizationMiddleware,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from shared import get_current_profile, get_pull_requests, get_user_info, create_profile_card, create_pr_card

logger = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.message(re.compile(r"^/(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState) -> bool:
    """
    Internal method to check authorization status for all configured handlers.
    Returns True if at least one handler has a valid token.
    """
    await context.send_activity(MessageFactory.text("Welcome to the auto-signin demo"))
    tok_graph = await AGENT_APP.auth.get_token(context, "GRAPH")
    tok_github = await AGENT_APP.auth.get_token(context, "GITHUB")
    status_graph = tok_graph.token is not None
    status_github = tok_github.token is not None
    await context.send_activity(
        MessageFactory.text(
            f"Graph status: {'Connected' if status_graph else 'Not connected'}\n"
            f"GitHub status: {'Connected' if status_github else 'Not connected'}"
        )
    )


@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    await AGENT_APP.auth.sign_out(context, "GRAPH")
    await AGENT_APP.auth.sign_out(context, "GITHUB")
    await context.send_activity(MessageFactory.text("You have been logged out."))


@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")
    if user_token_response:
        user_info = await get_user_info(user_token_response.token)
        activity = MessageFactory.attachment(create_profile_card(user_info))
        await context.send_activity(activity)
    else:
        await context.send_activity(
            MessageFactory.text('Token not available. Enter "login" to sign in.')
        )


@AGENT_APP.message(
    re.compile(r"^/(prs|pull requests)$", re.IGNORECASE), auth_handlers=["GITHUB"]
)
async def pull_requests(context: TurnContext, state: TurnState) -> None:
    user_token_response = await AGENT_APP.auth.get_token(context, "GITHUB")
    if user_token_response and user_token_response is not None:
        gh_prof = await get_current_profile(user_token_response.token)
        await context.send_activity(
            MessageFactory.attachment(create_profile_card(gh_prof))
        )

        # prs = await get_pull_requests("microsoft", "agents", user_token_response.token)
        # as suggested by Copilot, using a public repository without SAML enforcement
        prs = await get_pull_requests(
            "octocat", "Hello-World", user_token_response.token
        )
        for pr in prs:
            card = create_pr_card(pr)
            await context.send_activity(MessageFactory.attachment(card))
    else:
        token_response = await AGENT_APP.auth.begin_or_continue_flow(
            context, state, "GITHUB"
        )
        logger.warning(f"GitHub token: {json.dumps(token_response)}")
        if token_response and token_response.token is not None:
            await context.send_activity(
                MessageFactory.text(f"GitHub token length: {len(token_response.token)}")
            )
        else:
            await context.send_activity(
                MessageFactory.text("Failed to obtain GitHub token.")
            )


@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(MessageFactory.text("Invoke activity received."))


@AGENT_APP.activity(ActivityTypes.message)
async def message(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        MessageFactory.text(f"You said: {context.activity.text}")
    )


# Create FastAPI app
app = FastAPI(title="Authorization Agent Sample", version="1.0.0")
app.state.agent_configuration = (
    CONNECTION_MANAGER.get_default_connection_configuration()
)
app.add_middleware(JwtAuthorizationMiddleware)


# FastAPI routes
@app.post("/api/messages")
async def messages_handler(
    request: Request,
):
    """Main endpoint for processing bot messages."""

    return await start_agent_process(
        request,
        AGENT_APP,
        AGENT_APP.adapter,
    )


@app.get("/api/messages")
async def messages_get():
    """Health check endpoint."""
    return {"status": "OK"}


if __name__ == "__main__":
    port = int(environ.get("PORT", 3978))
    uvicorn.run(app, host="0.0.0.0", port=port)

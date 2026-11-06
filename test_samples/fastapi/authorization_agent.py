# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from os import environ, path
import re

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
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
    jwt_authorization_decorator,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from shared import (
    get_current_profile,
    get_pull_requests,
    get_user_info,
    create_profile_card,
    create_pr_card,
)

logger = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(config=agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, settings=agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](storage=STORAGE, authorization=AUTHORIZATION)
AUTH_HANDLER_IDS = ("GRAPH", "GITHUB", "MCS")


@AGENT_APP.message(re.compile(r"^/(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState):
    """Report token availability without starting a sign-in flow."""
    status_messages = []
    for handler_id in AUTH_HANDLER_IDS:
        token_response = await AGENT_APP.auth.get_token(context, handler_id)
        connected = bool(token_response and token_response.token)
        status_messages.append(
            f"{handler_id}: {'Connected' if connected else 'Not connected'}"
        )
    await context.send_activity(
        MessageFactory.text("Authorization Status:\n" + "\n".join(status_messages))
    )


@AGENT_APP.message("/login", auth_handlers=["GRAPH", "GITHUB"])
async def login(context: TurnContext, state: TurnState) -> None:
    await context.send_activity("You are signed in to Graph and GitHub.")


@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    for handler_id in AUTH_HANDLER_IDS:
        await AGENT_APP.auth.sign_out(context, handler_id)
    await context.send_activity(MessageFactory.text("You have been logged out."))


@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")
    if user_token_response and user_token_response.token:
        user_info = await get_user_info(user_token_response.token)
        activity = MessageFactory.attachment(create_profile_card(user_info))
        await context.send_activity(activity)
    else:
        await context.send_activity(
            MessageFactory.text(
                "Graph token not available. Send '/profile' to sign in again."
            )
        )


@AGENT_APP.message(
    re.compile(r"^/(prs|pull requests)$", re.IGNORECASE), auth_handlers=["GITHUB"]
)
async def pull_requests(context: TurnContext, state: TurnState) -> None:
    user_token_response = await AGENT_APP.auth.get_token(context, "GITHUB")
    if user_token_response and user_token_response.token:
        gh_prof = await get_current_profile(user_token_response.token)
        await context.send_activity(
            MessageFactory.attachment(create_profile_card(gh_prof))
        )

        prs = await get_pull_requests(
            "octocat", "Hello-World", user_token_response.token
        )
        if not prs:
            await context.send_activity("No open pull requests found.")
        for pr in prs:
            card = create_pr_card(pr)
            await context.send_activity(MessageFactory.attachment(card))
    else:
        await context.send_activity(
            "GitHub token not available. Send '/prs' to sign in again."
        )


@AGENT_APP.activity(ActivityTypes.message)
async def message(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        MessageFactory.text(f"You said: {context.activity.text}")
    )


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception) -> None:
    logger.error(
        "Authorization request failed",
        exc_info=(type(error), error, error.__traceback__),
    )
    await context.send_activity("The agent encountered an error. Please try again.")


# Create FastAPI app
app = FastAPI(title="Authorization Agent Sample", version="1.0.0")
app.state.agent_configuration = agents_sdk_config


# FastAPI routes
@app.post("/api/messages")
@jwt_authorization_decorator
async def messages_handler(
    request: Request,
):
    """Main endpoint for processing bot messages."""

    return await start_agent_process(
        request,
        AGENT_APP,
        ADAPTER,
    )


@app.get("/api/messages")
async def messages_get():
    """Health check endpoint."""
    return {"status": "OK"}


if __name__ == "__main__":
    port = agents_sdk_config.get_int("PORT", default=3978)
    uvicorn.run(app, host="0.0.0.0", port=port)

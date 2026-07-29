# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from os import environ

from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    start_agent_process,
    jwt_authorization_decorator,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

# Create the agent application

load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

# Create FastAPI app
app = FastAPI(title="Empty Agent Sample", version="1.0.0")
app.state.agent_configuration = (
    CONNECTION_MANAGER.get_default_connection_configuration()
)


# Agent handlers
async def _help(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the Empty Agent Sample 🚀. "
        "Type /help for help or send a message to see the echo feature in action."
    )


AGENT_APP.conversation_update("membersAdded")(_help)
AGENT_APP.message("/help")(_help)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _):
    await context.send_activity(f"you said: {context.activity.text}")


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
        AGENT_APP.adapter,
    )


@app.get("/api/messages")
async def messages_get():
    """Health check endpoint."""
    return {"status": "OK"}


if __name__ == "__main__":

    port = int(environ.get("PORT", 3978))
    uvicorn.run(app, host="127.0.0.1", port=port)

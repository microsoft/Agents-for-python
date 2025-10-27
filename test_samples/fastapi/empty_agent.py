# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import uvicorn
from fastapi import FastAPI, Request, Depends
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    start_agent_process,
    JwtAuthorizationMiddleware,
)

# Create the agent application
AGENT_APP = AgentApplication[TurnState](storage=MemoryStorage(), adapter=CloudAdapter())

# Create FastAPI app
app = FastAPI(title="Empty Agent Sample", version="1.0.0")
app.add_middleware(JwtAuthorizationMiddleware)


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
    import os

    port = int(os.environ.get("PORT", 3978))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from dotenv import load_dotenv

from os import environ
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.hosting.core.storage import (
    TranscriptLoggerMiddleware,
    ConsoleTranscriptLogger,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

logger = logging.getLogger(__name__)

load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
ADAPTER.use(TranscriptLoggerMiddleware(ConsoleTranscriptLogger()))
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.activity("message", auth_handlers=["AGENTIC"])
async def on_message(context: TurnContext, _state: TurnState):
    aau_token = await AGENT_APP.auth.get_token(context, "AGENTIC")
    await context.send_activity(
        f"Acquired agentic user token with length: {len(aau_token.token)}"
    )


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    logger.error("[on_turn_error] unhandled error: %s", error)

    # Send a message to the user
    await context.send_activity("The agent encountered an error.")

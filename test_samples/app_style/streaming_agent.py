# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
from os import environ
import re
import sys
import traceback

from dotenv import load_dotenv
from microsoft.agents.builder.app import AgentApplication, TurnState
from microsoft.agents.builder.app.oauth import Authorization
from microsoft.agents.hosting.aiohttp import CloudAdapter, Citation
from microsoft.agents.authentication.msal import MsalConnectionManager

from microsoft.agents.builder import (
    TurnContext,
    MessageFactory,
)
from microsoft.agents.storage import MemoryStorage
from microsoft.agents.core import load_configuration_from_env
from microsoft.agents.core.models import Activity, ActivityTypes, SensitivityUsageInfo

from shared import start_server

load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> str:
    """
    Internal method to process template expansion or function invocation.
    """
    invoke_response = Activity(
        type=ActivityTypes.invoke_response, value={"status": 200}
    )
    print(f"Invoke activity received: {context.activity}")
    await context.send_activity(invoke_response)


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the Streaming sample, send a message to see the streaming feature in action."
    )
    return True


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    context.streaming_response.set_feedback_loop(True)
    context.streaming_response.set_sensitivity_label(
        SensitivityUsageInfo(
            type="https://schema.org/Message",
            schema_type="CreativeWork",
            name="Internal",
        )
    )
    context.streaming_response.set_generated_by_ai_label(True)
    context.streaming_response.queue_informative_update("starting streaming response")
    await asyncio.sleep(1)

    for i in range(5):
        print(f"Streaming chunk {i + 1}")
        context.streaming_response.queue_text_chunk(f"part [{i + 1}] ")
        await asyncio.sleep(i * 0.5)

    context.streaming_response.queue_text_chunk(
        "This is the final message part. [doc1] and [doc2]"
    )
    context.streaming_response.set_citations(
        [
            Citation(title="Citation1", content="file", filepath="", url="file:////"),
            Citation(
                title="Citation2",
                content="loooonger content",
                filepath="",
                url="file:////",
            ),
        ]
    )

    await context.streaming_response.end_stream()


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")


start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)

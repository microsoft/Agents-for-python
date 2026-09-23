# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from a2a.types import AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI

from microsoft_agents.hosting.a2a import A2AAdapter, add_a2a
from microsoft_agents.activity import Activity, ActivityTypes, EndOfConversationCodes
from microsoft_agents.hosting.core import (
    AgentApplication,
    ApplicationOptions,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from tests._common.testing_objects import TestingConnectionManager

STREAMING_TRIGGER_TEXT = "stream-me"
"""Message text that causes the test agent to emit chunked streaming updates."""

INPUT_REQUIRED_TRIGGER_TEXT = "need-more-input"
"""Message text that leaves the task waiting for a continuation."""

STRUCTURED_RESULT_TRIGGER_TEXT = "structured-result"
"""Message text that completes with both text and structured result data."""


def _create_agent_application() -> AgentApplication[TurnState]:
    application = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=TestingConnectionManager(),
    )

    @application.activity("message")
    async def on_message(context: TurnContext, _state: TurnState) -> None:
        text = context.activity.text or ""
        if text == STREAMING_TRIGGER_TEXT:
            # Exercise the chunked streaming API so that informative and
            # partial-content updates surface as A2A task status/artifact
            # update events.
            streaming_response = context.streaming_response
            streaming_response.queue_informative_update("Thinking...")
            streaming_response.queue_text_chunk("Echo: ")
            streaming_response.queue_text_chunk(text)
            await streaming_response.end_stream()
        elif text == INPUT_REQUIRED_TRIGGER_TEXT:
            await context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text="More information required",
                    input_hint="expectingInput",
                )
            )
            return
        elif text == STRUCTURED_RESULT_TRIGGER_TEXT:
            await context.send_activity(
                Activity(
                    type=ActivityTypes.end_of_conversation,
                    code=EndOfConversationCodes.completed_successfully,
                    text="Completed with structured data",
                    value={"answer": 42},
                )
            )
            return
        else:
            await context.send_activity(f"Echo: {text}")
        await context.send_activity(
            Activity(
                type=ActivityTypes.end_of_conversation,
                code=EndOfConversationCodes.completed_successfully,
            )
        )

    return application


@pytest_asyncio.fixture
async def a2a_client() -> AsyncIterator[httpx.AsyncClient]:
    """Create an unauthenticated application exposing JSON-RPC and REST A2A routes."""

    app = FastAPI()
    agent = _create_agent_application()
    adapter = A2AAdapter(
        agent,
        agent_card_name="Compatibility Agent",
        agent_card_description="A deterministic A2A compatibility test agent.",
        agent_card_version="1.0.0",
        agent_interfaces=[
            AgentInterface(
                url="/rpc",
                protocol_binding=TransportProtocol.JSONRPC,
            ),
            AgentInterface(
                url="/rest",
                protocol_binding=TransportProtocol.HTTP_JSON,
            ),
        ],
        skills=[
            AgentSkill(
                id="echo",
                name="Echo",
                description="Echoes the incoming text.",
                tags=["test"],
                examples=["Hello"],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )
    add_a2a(app, agent, adapter=adapter, use_jwt_middleware=False)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

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


def _create_agent_application() -> AgentApplication[TurnState]:
    application = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=TestingConnectionManager(),
    )

    @application.activity("message")
    async def on_message(context: TurnContext, _state: TurnState) -> None:
        await context.send_activity(f"Echo: {context.activity.text or ''}")
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

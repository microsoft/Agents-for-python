# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import argparse
import asyncio
from uuid import uuid4

import uvicorn
from a2a.types import AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI
from starlette.routing import Route

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Attachment,
    EndOfConversationCodes,
    InputHints,
    StreamInfo,
)
from microsoft_agents.hosting.a2a import A2AAdapter, add_a2a
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    AnonymousTokenProvider,
    ApplicationOptions,
    ConnectionManager,
    MemoryStorage,
    TurnContext,
    TurnState,
)


def create_agent() -> AgentApplication[TurnState]:
    connection_manager = ConnectionManager(
        provider_factory=lambda _: AnonymousTokenProvider(),
        connections_configurations={
            "SERVICE_CONNECTION": AgentAuthConfiguration(
                anonymous_allowed=True,
            )
        },
    )
    application = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=connection_manager,
    )

    @application.activity("message")
    async def on_message(context: TurnContext, _state: TurnState) -> None:
        message_id = getattr(context.activity.channel_data, "message_id", "")

        async def send_artifact(
            *,
            text: str | None = None,
            value: dict | None = None,
            attachment: Attachment | None = None,
        ) -> None:
            await context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text=text,
                    value=value,
                    attachments=[attachment] if attachment else [],
                    entities=[
                        StreamInfo(
                            stream_id=str(uuid4()),
                            stream_type="content",
                            stream_sequence=1,
                        )
                    ],
                )
            )

        if message_id.startswith("test-resubscribe-message-id"):
            await context.send_activity("Working")
            await asyncio.sleep(4)
        elif message_id.startswith("tck-input-required"):
            await context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    input_hint=InputHints.expecting_input,
                )
            )
            return
        elif message_id.startswith("tck-message-response"):
            await context.send_activity("Direct message response")
            return
        elif message_id.startswith("tck-artifact-file-url"):
            await send_artifact(
                attachment=Attachment(
                    content_type="text/plain",
                    content_url="https://example.com/output.txt",
                    name="output.txt",
                )
            )
        elif message_id.startswith("tck-artifact-file"):
            await send_artifact(
                attachment=Attachment(
                    content_type="text/plain",
                    content=b"tck",
                    name="output.txt",
                )
            )
        elif message_id.startswith("tck-artifact-data"):
            await send_artifact(value={"key": "value", "count": 42})
        elif message_id.startswith("tck-artifact-text"):
            await send_artifact(text="Generated text content")
        elif message_id.startswith("tck-stream-artifact-chunked"):
            response = context.streaming_response
            response.queue_text_chunk("chunk-1 ")
            response.queue_text_chunk("chunk-2")
            await response.end_stream()
            return
        elif message_id.startswith("tck-stream-artifact-file"):
            await send_artifact(
                attachment=Attachment(
                    content_type="text/plain",
                    content=b"tck",
                    name="output.txt",
                )
            )
        elif message_id.startswith("tck-stream-artifact-text"):
            response = context.streaming_response
            response.queue_text_chunk("Streamed text content")
            await response.end_stream()
            return
        elif message_id.startswith("tck-stream-ordering-001"):
            response = context.streaming_response
            response.queue_informative_update("Working")
            response.queue_text_chunk("Ordered output")
            await response.end_stream()
            return
        elif message_id.startswith("tck-stream-001"):
            response = context.streaming_response
            response.queue_text_chunk("Stream hello from TCK")
            await response.end_stream()
            return
        elif message_id.startswith("tck-stream-002"):
            pass
        elif message_id.startswith("tck-stream-003"):
            response = context.streaming_response
            response.queue_informative_update("Working")
            response.queue_text_chunk("Stream task lifecycle")
            await response.end_stream()
            return
        else:
            await context.send_activity("Hello from TCK")

        await context.send_activity(
            Activity(
                type=ActivityTypes.end_of_conversation,
                code=EndOfConversationCodes.completed_successfully,
            )
        )

    return application


def create_app() -> FastAPI:
    agent = create_agent()
    adapter = A2AAdapter(
        agent,
        agent_card_name="Microsoft Agents SDK TCK Agent",
        agent_card_description="A deterministic agent for A2A TCK validation.",
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
                description="Echoes incoming text.",
                tags=["test", "echo"],
                examples=["Hello"],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )

    app = FastAPI(title="Microsoft Agents SDK A2A TCK Agent", version="1.0.0")
    add_a2a(
        app,
        agent,
        adapter=adapter,
        use_jwt_middleware=False,
    )

    rpc_route = next(
        route
        for route in app.router.routes
        if isinstance(route, Route) and route.path == "/rpc"
    )
    mount_index = next(
        index
        for index, route in enumerate(app.router.routes)
        if route.path == "/{tenant}"
    )
    app.router.routes.insert(
        mount_index,
        Route(
            path="/rpc/",
            endpoint=rpc_route.endpoint,
            methods=["POST"],
        ),
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local A2A TCK agent.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=41241, type=int)
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()

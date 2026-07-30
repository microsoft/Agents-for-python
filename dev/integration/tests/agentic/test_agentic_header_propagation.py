# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Integration tests for agentic header propagation."""

import asyncio

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import Activity, ActivityTypes, RoleTypes
from microsoft_agents.hosting.aiohttp import CloudAdapter, start_agent_process
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    ApplicationOptions,
    Authorization,
    ConnectorClientBase,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity


class _FakeTokenProvider:
    def __init__(self):
        self._configuration = AgentAuthConfiguration()

    @property
    def configuration(self) -> AgentAuthConfiguration:
        return self._configuration

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return "test-access-token"

    async def get_agentic_user_token(
        self,
        tenant_id: str,
        agent_app_instance_id: str,
        agentic_user_id: str,
        scopes: list[str],
    ) -> str:
        return "test-agentic-user-token"


class _FakeConnections:
    def __init__(self):
        self._provider = _FakeTokenProvider()

    def get_connection(self, connection_name: str):
        return self._provider

    def get_default_connection(self):
        return self._provider

    def get_token_provider(self, claims_identity: ClaimsIdentity, service_url: str):
        return self._provider

    def get_token_provider_from_activity(
        self, claims_identity: ClaimsIdentity, activity: Activity
    ):
        return self._provider

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        return self._provider.configuration


@pytest.mark.asyncio
async def test_agentic_turn_propagates_headers_on_connector_client_request():
    captured_headers = {}
    callback_received = asyncio.Event()

    async def callback_handler(request: web.Request) -> web.Response:
        captured_headers.update(dict(request.headers))
        callback_received.set()
        return web.json_response({"id": "connector-response-id"})

    callback_app = web.Application()
    callback_app.router.add_post("/v3/conversations/{tail:.*}", callback_handler)
    callback_server = TestServer(callback_app)
    await callback_server.start_server()

    connection_manager = _FakeConnections()
    storage = MemoryStorage()
    adapter = CloudAdapter(connection_manager=connection_manager)
    agent_application = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=storage,
            start_typing_timer=False,
            remove_recipient_mention=False,
        ),
        authorization=Authorization(storage, connection_manager),
        agent_name="Agentic Header Test Agent",
    )

    @agent_application.activity(ActivityTypes.message)
    async def on_message(context: TurnContext, state: TurnState) -> None:
        connector_client = context.services.get(ConnectorClientBase)
        assert connector_client is not None

        await connector_client.conversations.send_to_conversation(
            context.activity.conversation.id,
            Activity(type=ActivityTypes.message, text="connector client response"),
        )

    agent_app = web.Application()

    async def messages(request: web.Request) -> web.Response:
        return await start_agent_process(
            request,
            agent_application=agent_application,
            adapter=adapter,
        )

    agent_app.router.add_post("/api/messages", messages)
    agent_server = TestServer(agent_app)
    await agent_server.start_server()

    try:
        activity = Activity(
            type=ActivityTypes.message,
            text="send with connector client",
            channel_id="msteams:Copilot",
            service_url=str(callback_server.make_url("/")),
            conversation={"id": "conversation-id"},
            from_property={"id": "user-id", "role": RoleTypes.user},
            recipient={
                "id": "agent-id",
                "role": RoleTypes.agentic_user,
                "agentic_app_id": "Entra:agentic-app-id",
                "agentic_user_id": "agentic-user-id",
                "tenant_id": "tenant-id",
            },
        )

        async with ClientSession() as session:
            async with session.post(
                agent_server.make_url("/api/messages"),
                json=activity.model_dump(
                    by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
                ),
            ) as response:
                assert response.status == 202

        await asyncio.wait_for(callback_received.wait(), timeout=5)

        assert captured_headers["AgentRegistrar"] == "A365"
        assert captured_headers["AgentID"] == "Entra:agentic-app-id"
        assert captured_headers["AgentName"] == "Agentic Header Test Agent"
        assert captured_headers["Agent-Referrer"] == "msteams:Copilot"
    finally:
        await agent_server.close()
        await callback_server.close()

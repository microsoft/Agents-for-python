# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import cast

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from microsoft_agents.activity import Activity, ConversationAccount
from microsoft_agents.hosting.core import OutboundHostValidator, TurnContext
from microsoft_agents.hosting.core.authorization import ClaimsIdentity, Connections
from microsoft_agents.hosting.core.connector.client import UserTokenClient
from microsoft_agents.hosting.fastapi import CloudAdapter


class RecordingAgent:
    def __init__(self):
        self.turn_count = 0

    async def on_turn(self, context: TurnContext):
        self.turn_count += 1


def _create_client(host_validator: OutboundHostValidator):
    adapter = CloudAdapter(
        connection_manager=cast(Connections, object()),
        host_validator=host_validator,
    )
    agent = RecordingAgent()
    app = FastAPI()

    @app.post("/api/messages")
    async def messages(request: Request):
        return await adapter.process(request, agent)

    return TestClient(app), agent


@pytest.mark.parametrize(
    ("host_validator", "service_url", "expected_status", "expected_turn_count"),
    [
        pytest.param(
            OutboundHostValidator(enabled=False),
            "https://evil.example.com/relay",
            202,
            1,
            id="disabled-allows-unknown-host",
        ),
        pytest.param(
            OutboundHostValidator(enabled=True),
            "https://smba.trafficmanager.net/teams/",
            202,
            1,
            id="enabled-allows-default-microsoft-host",
        ),
        pytest.param(
            OutboundHostValidator(enabled=True),
            "https://evil.example.com/relay",
            401,
            0,
            id="enabled-denies-unknown-host",
        ),
        pytest.param(
            OutboundHostValidator(
                enabled=True,
                hosts=["contoso.com"],
                include_default_microsoft_hosts=False,
            ),
            "https://api.contoso.com/messages",
            202,
            1,
            id="enabled-allows-configured-host",
        ),
        pytest.param(
            OutboundHostValidator(
                enabled=True,
                hosts=["contoso.com"],
                include_default_microsoft_hosts=False,
            ),
            "https://graph.microsoft.com/v1.0",
            401,
            0,
            id="enabled-without-defaults-denies-microsoft-host",
        ),
    ],
)
def test_cloud_adapter_applies_outbound_host_validator(
    host_validator: OutboundHostValidator,
    service_url: str,
    expected_status: int,
    expected_turn_count: int,
):
    client, agent = _create_client(host_validator)

    response = client.post(
        "/api/messages",
        json={
            "type": "message",
            "conversation": {"id": "conversation-id"},
            "serviceUrl": service_url,
        },
    )

    assert response.status_code == expected_status
    assert agent.turn_count == expected_turn_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_service_endpoint",
    [
        "https://europe.api.botframework.com",
        "https://unitedstates.api.botframework.com",
        "https://india.api.botframework.com",
    ],
)
async def test_cloud_adapter_configures_user_token_client_endpoint(
    token_service_endpoint: str,
):
    adapter = CloudAdapter(
        connection_manager=cast(Connections, object()),
        channel_service_client_factory_options={
            "token_service_endpoint": token_service_endpoint
        },
    )
    identity = ClaimsIdentity({"aud": "test-app-id"}, True)
    context = TurnContext(
        adapter,
        Activity(
            type="message",
            conversation=ConversationAccount(id="conversation-id"),
        ),
        identity,
    )

    client = await adapter._channel_service_client_factory.create_user_token_client(
        context,
        identity,
        use_anonymous=True,
    )
    assert isinstance(client, UserTokenClient)
    try:
        assert str(client.client._base_url) == f"{token_service_endpoint}/"
    finally:
        await client.close()

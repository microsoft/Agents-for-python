# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import cast

import pytest

from microsoft_agents.activity import Activity, ConversationAccount
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.authorization import ClaimsIdentity, Connections
from microsoft_agents.hosting.core.connector.client import UserTokenClient
from microsoft_agents.hosting.fastapi import CloudAdapter


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

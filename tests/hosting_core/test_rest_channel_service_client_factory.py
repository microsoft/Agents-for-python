# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock

from microsoft_agents.activity import Activity, RoleTypes, ChannelAccount
from microsoft_agents.hosting.core import (
    RestChannelServiceClientFactory,
    TurnContext,
)
from microsoft_agents.hosting.core.authorization import (
    AuthenticationConstants,
    ClaimsIdentity,
    Connections,
    AccessTokenProviderBase,
)
from microsoft_agents.hosting.core.connector.teams import TeamsConnectorClient
from microsoft_agents.hosting.core.connector.client import UserTokenClient

from tests._common.data import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()


class TestRestChannelServiceClientFactory:

    
    @pytest.mark.parametrize(
        "token_service_endpoint, token_service_audience",
        [
            (AuthenticationConstants.AGENTS_SDK_OAUTH_URL, AuthenticationConstants.AGENTS_SDK_SCOPE),
            ("https://custom.token.endpoint", "https://custom.token.audience"),
        ]
    )
    @pytest.mark.asyncio
    async def test_create_connector_client_anonymous(
        self, 
        mocker,
        token_service_endpoint,
        token_service_audience
    ):
        # setup
        token_provider = mocker.mock(spec=AccessTokenProviderBase)
        token_provider.get_access_token = AsyncMock(return_value=DEFAULTS.token)

        connection_manager = mocker.mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(
            return_value=token_provider
        )

        factory = RestChannelServiceClientFactory(
            connection_manager,
            token_service_endpoint,
            token_service_audience
        )

        activity = Activity(
            type="message",
        )
        
        claims_identity = ClaimsIdentity(
            {

            },

        )

        context = TurnContext(

        )

        res = await factory.create_connector_client(
            context,
            claims_identity,
            service_url,
            audience,
            scopes,
            use_anynoymous=True,
        )
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

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
    AnonymousTokenProvider,
    AgentAuthConfiguration,
)
from microsoft_agents.hosting.core.connector.teams import TeamsConnectorClient
from microsoft_agents.hosting.core.connector.client import UserTokenClient

from tests._common.data import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()


class TestRestChannelServiceClientFactory:

    @pytest.fixture
    def activity(self):
        return Activity(
            type="message",
            channel_id="msteams",
            from_property=ChannelAccount(id="user1", role=RoleTypes.user),
            recipient=ChannelAccount(id="bot1", role=RoleTypes.agent),
            service_url="https://service.url/",
            conversation={"id": "conv1"},
            id="activity1",
            text="Hello, World!",
        )

    @pytest.fixture(params=[True, False])
    def context_flag(self, request):
        return request.param

    @pytest.fixture
    def activity_agentic_user(self):
        return Activity(
            type="message",
            channel_id="msteams",
            from_property=ChannelAccount(id="agentic_user", role=RoleTypes.user),
            recipient=ChannelAccount(
                id="bot1",
                agentic_app_id="agentic_app_id",
                agentic_user_id="agentic_user_id",
                role=RoleTypes.agentic_user,
            ),
            service_url="https://service.url/",
            conversation={"id": "conv1"},
            id="activity_agentic1",
            text="Hello, World!",
            properties={"agenticRequest": True},
        )

    @pytest.fixture
    def activity_agentic_identity(self):
        return Activity(
            type="message",
            channel_id="msteams",
            from_property=ChannelAccount(id="agentic_user", role=RoleTypes.user),
            recipient=ChannelAccount(
                id="bot1",
                agentic_app_id="agentic_app_id",
                role=RoleTypes.agentic_identity,
            ),
            service_url="https://service.url/",
            conversation={"id": "conv1"},
            id="activity_agentic1",
            text="Hello, World!",
            properties={"agenticRequest": True},
        )

    @pytest.mark.parametrize(
        "token_service_endpoint, token_service_audience",
        [
            (
                AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
                AuthenticationConstants.AGENTS_SDK_SCOPE,
            ),
            ("https://custom.token.endpoint", "https://custom.token.audience"),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_connector_client_anonymous(
        self,
        mocker,
        activity,
        token_service_endpoint,
        token_service_audience,
        context_flag,
    ):
        mock_connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=mock_connector_client
        )

        factory = RestChannelServiceClientFactory(
            mocker.Mock(spec=Connections),
            token_service_endpoint,
            token_service_audience,
        )

        context = mocker.Mock(spec=TurnContext)
        context.activity = activity
        claims_identity = mocker.Mock(spec=ClaimsIdentity)
        scopes = ["scope1"]
        audience = "https://service.audience/"

        res = await factory.create_connector_client(
            context if context_flag else None,
            claims_identity,
            DEFAULTS.service_url,
            audience,
            scopes,
            use_anonymous=True,
        )

        # verify
        TeamsConnectorClient.__new__.assert_called_once_with(
            TeamsConnectorClient, endpoint=DEFAULTS.service_url, token=""
        )
        assert res == mock_connector_client

    @pytest.mark.parametrize(
        "token_service_endpoint, token_service_audience",
        [
            (
                AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
                AuthenticationConstants.AGENTS_SDK_SCOPE,
            ),
            ("https://custom.token.endpoint", "https://custom.token.audience"),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_connector_client_normal_no_scopes(
        self,
        mocker,
        activity,
        token_service_endpoint,
        token_service_audience,
        context_flag,
    ):
        # setup
        mock_connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=mock_connector_client
        )

        token_provider = mocker.Mock(spec=AccessTokenProviderBase)
        token_provider.get_access_token = mocker.AsyncMock(return_value=DEFAULTS.token)

        connection_manager = mocker.Mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(return_value=token_provider)

        factory = RestChannelServiceClientFactory(
            connection_manager, token_service_endpoint, token_service_audience
        )

        claims_identity = mocker.Mock(spec=ClaimsIdentity)
        service_url = DEFAULTS.service_url
        audience = "https://service.audience/"

        context = mocker.Mock(spec=TurnContext)
        context.activity = activity

        # test

        res = await factory.create_connector_client(
            context if context_flag else None,
            claims_identity,
            service_url,
            audience,
            None,
        )

        # verify
        assert connection_manager.get_token_provider.call_count == 1
        connection_manager.get_token_provider.assert_called_once_with(
            claims_identity, service_url
        )
        assert token_provider.get_access_token.call_count == 1
        token_provider.get_access_token.assert_called_once_with(
            audience, [f"{audience}/.default"]
        )
        TeamsConnectorClient.__new__.assert_called_once_with(
            TeamsConnectorClient, endpoint=DEFAULTS.service_url, token=DEFAULTS.token
        )

    @pytest.mark.parametrize(
        "token_service_endpoint, token_service_audience",
        [
            (
                AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
                AuthenticationConstants.AGENTS_SDK_SCOPE,
            ),
            ("https://custom.token.endpoint", "https://custom.token.audience"),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_connector_client_normal(
        self,
        mocker,
        activity,
        token_service_endpoint,
        token_service_audience,
        context_flag,
    ):
        # setup
        mock_connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=mock_connector_client
        )

        token_provider = mocker.Mock(spec=AccessTokenProviderBase)
        token_provider.get_access_token = mocker.AsyncMock(return_value=DEFAULTS.token)

        connection_manager = mocker.Mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(return_value=token_provider)

        factory = RestChannelServiceClientFactory(
            connection_manager, token_service_endpoint, token_service_audience
        )

        claims_identity = mocker.Mock(spec=ClaimsIdentity)
        service_url = DEFAULTS.service_url
        audience = "https://service.audience/"
        scopes = ["scope1", "scope2"]

        context = mocker.Mock(spec=TurnContext)
        context.activity = activity

        # test

        res = await factory.create_connector_client(
            context if context_flag else None,
            claims_identity,
            service_url,
            audience,
            scopes,
        )

        # verify
        assert connection_manager.get_token_provider.call_count == 1
        connection_manager.get_token_provider.assert_called_once_with(
            claims_identity, service_url
        )
        assert token_provider.get_access_token.call_count == 1
        token_provider.get_access_token.assert_called_once_with(audience, scopes)
        TeamsConnectorClient.__new__.assert_called_once_with(
            TeamsConnectorClient, endpoint=DEFAULTS.service_url, token=DEFAULTS.token
        )

    @pytest.mark.parametrize("alt_blueprint", [True, False])
    @pytest.mark.asyncio
    async def test_create_connector_client_agentic_identity(
        self, mocker, activity_agentic_identity, alt_blueprint
    ):
        # setup
        mock_connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=mock_connector_client
        )

        token_provider = mocker.Mock(spec=AccessTokenProviderBase)
        token_provider.get_agentic_instance_token = mocker.AsyncMock(
            return_value=(DEFAULTS.token, None)
        )

        connection_manager = mocker.Mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(return_value=token_provider)

        auth_config = AgentAuthConfiguration()
        if alt_blueprint:
            auth_config.ALT_BLUEPRINT_ID = "alt_blueprint_id"
            connection_manager.get_connection = mocker.Mock(return_value=token_provider)
        token_provider._msal_configuration = auth_config

        factory = RestChannelServiceClientFactory(connection_manager)

        claims_identity = mocker.Mock(spec=ClaimsIdentity)
        service_url = DEFAULTS.service_url
        audience = "https://service.audience/"
        scopes = ["scope1", "scope2"]

        context = mocker.Mock(spec=TurnContext)
        context.activity = activity_agentic_identity

        # test

        res = await factory.create_connector_client(
            context,
            claims_identity,
            service_url,
            audience,
            scopes,
        )

        # verify
        assert connection_manager.get_token_provider.call_count == 1
        connection_manager.get_token_provider.assert_called_once_with(
            context.identity, service_url
        )
        if alt_blueprint:
            connection_manager.get_connection.assert_called_once_with(
                "alt_blueprint_id"
            )
        assert token_provider.get_agentic_instance_token.call_count == 1
        token_provider.get_agentic_instance_token.assert_called_once_with(
            "agentic_app_id"
        )
        TeamsConnectorClient.__new__.assert_called_once_with(
            TeamsConnectorClient, endpoint=DEFAULTS.service_url, token=DEFAULTS.token
        )

    @pytest.mark.parametrize("alt_blueprint", [True, False])
    @pytest.mark.asyncio
    async def test_create_connector_client_agentic_user(
        self, mocker, activity_agentic_user, alt_blueprint
    ):
        # setup
        mock_connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=mock_connector_client
        )

        token_provider = mocker.Mock(spec=AccessTokenProviderBase)
        token_provider.get_agentic_user_token = mocker.AsyncMock(
            return_value=DEFAULTS.token
        )

        connection_manager = mocker.Mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(return_value=token_provider)

        auth_config = AgentAuthConfiguration()
        if alt_blueprint:
            auth_config.ALT_BLUEPRINT_ID = "alt_blueprint_id"
            connection_manager.get_connection = mocker.Mock(return_value=token_provider)
        token_provider._msal_configuration = auth_config

        factory = RestChannelServiceClientFactory(connection_manager)

        claims_identity = mocker.Mock(spec=ClaimsIdentity)
        service_url = DEFAULTS.service_url
        audience = "https://service.audience/"
        scopes = ["scope1", "scope2"]

        context = mocker.Mock(spec=TurnContext)
        context.activity = activity_agentic_user

        # test

        res = await factory.create_connector_client(
            context,
            claims_identity,
            service_url,
            audience,
            scopes,
        )

        # verify
        assert connection_manager.get_token_provider.call_count == 1
        connection_manager.get_token_provider.assert_called_once_with(
            context.identity, service_url
        )
        if alt_blueprint:
            connection_manager.get_connection.assert_called_once_with(
                "alt_blueprint_id"
            )
        assert token_provider.get_agentic_user_token.call_count == 1
        token_provider.get_agentic_user_token.assert_called_once_with(
            "agentic_app_id",
            "agentic_user_id",
            [AuthenticationConstants.APX_PRODUCTION_SCOPE],
        )
        TeamsConnectorClient.__new__.assert_called_once_with(
            TeamsConnectorClient, endpoint=DEFAULTS.service_url, token=DEFAULTS.token
        )

from typing import Optional

from microsoft.agents.hosting.core.authorization import (
    AuthenticationConstants,
    AnonymousTokenProvider,
    ClaimsIdentity,
    Connections,
)
from microsoft.agents.hosting.core.authorization import AccessTokenProviderBase
from microsoft.agents.hosting.core.connector import ConnectorClientBase
from microsoft.agents.hosting.core.connector.client import UserTokenClient
from microsoft.agents.hosting.core.connector.teams import TeamsConnectorClient

from .channel_service_client_factory_base import ChannelServiceClientFactoryBase


class RestChannelServiceClientFactory(ChannelServiceClientFactoryBase):
    _ANONYMOUS_TOKEN_PROVIDER = AnonymousTokenProvider()

    def __init__(
        self,
        connection_manager: Connections,
        token_service_endpoint=AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
        token_service_audience=AuthenticationConstants.AGENTS_SDK_SCOPE,
    ) -> None:
        self._connection_manager = connection_manager
        self._token_service_endpoint = token_service_endpoint
        self._token_service_audience = token_service_audience

    async def create_connector_client(
        self,
        claims_identity: ClaimsIdentity,
        service_url: str,
        audience: str,
        scopes: Optional[list[str]] = None,
        use_anonymous: bool = False,
    ) -> ConnectorClientBase:
        if not service_url:
            raise TypeError(
                "RestChannelServiceClientFactory.create_connector_client: service_url can't be None or Empty"
            )
        if not audience:
            raise TypeError(
                "RestChannelServiceClientFactory.create_connector_client: audience can't be None or Empty"
            )

        token_provider: AccessTokenProviderBase = (
            self._connection_manager.get_token_provider(claims_identity, service_url)
            if not use_anonymous
            else self._ANONYMOUS_TOKEN_PROVIDER
        )

        token = await token_provider.get_access_token(
            audience, scopes or [f"{audience}/.default"]
        )

        return TeamsConnectorClient(
            endpoint=service_url,
            token=token,
        )

    async def create_user_token_client(
        self, claims_identity: ClaimsIdentity, use_anonymous: bool = False
    ) -> UserTokenClient:
        token_provider = (
            self._connection_manager.get_token_provider(
                claims_identity, self._token_service_endpoint
            )
            if not use_anonymous
            else self._ANONYMOUS_TOKEN_PROVIDER
        )

        token = await token_provider.get_access_token(
            self._token_service_audience, [f"{self._token_service_audience}/.default"]
        )
        return UserTokenClient(
            endpoint=self._token_service_endpoint,
            token=token,
        )

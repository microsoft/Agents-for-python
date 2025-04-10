from typing import Any, Optional

from microsoft.agents.authorization import (
    AuthenticationConstants,
    AnonymousTokenProvider,
    ClaimsIdentity,
    Connections,
)
from microsoft.agents.authorization import AccessTokenProviderBase
from microsoft.agents.connector import (
    ConnectorClientBase,
    UserTokenClient,
)
from microsoft.agents.connector.client import ConnectorClient

from .channel_service_client_factory_base import ChannelServiceClientFactoryBase


class RestChannelServiceClientFactory(ChannelServiceClientFactoryBase):
    _ANONYMOUS_TOKEN_PROVIDER = AnonymousTokenProvider()

    def __init__(
        self,
        configuration: Any,
        connections: Connections,
        token_service_endpoint=AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
        token_service_audience=AuthenticationConstants.AGENTS_SDK_SCOPE,
    ) -> None:
        self._connections = connections
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
            self._connections.get_token_provider(claims_identity, service_url)
            if not use_anonymous
            else self._ANONYMOUS_TOKEN_PROVIDER
        )

        token = await token_provider.get_access_token(
            audience, scopes or [f"{audience}/.default"]
        )

        return ConnectorClient(
            endpoint=service_url,
            token=token,
        )

    async def create_user_token_client(
        self, claims_identity: ClaimsIdentity, use_anonymous: bool = False
    ) -> UserTokenClient:
        token_provider = (
            self._connections.get_token_provider(
                claims_identity, self._token_service_endpoint
            )
            if not use_anonymous
            else self._ANONYMOUS_TOKEN_PROVIDER
        )
        return UserTokenClient(
            credential_token_provider=token_provider,
            credential_resource_url=self._token_service_audience,
            credential_scopes=[f"{self._token_service_audience}/.default"],
            endpoint=self._token_service_endpoint,
        )

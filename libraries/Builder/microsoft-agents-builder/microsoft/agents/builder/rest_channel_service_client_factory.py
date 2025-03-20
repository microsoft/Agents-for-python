from typing import Any, Optional

from microsoft.agents.authentication import (
    AuthenticationConstants,
    ClaimsIdentity,
    Connections,
)
from microsoft.agents.connector import (
    ConnectorClientBase,
    ConnectorClient,
    UserTokenClient,
)

from .channel_service_client_factory_base import ChannelServiceClientFactoryBase


class RestChannelServiceClientFactory(ChannelServiceClientFactoryBase):
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

        return ConnectorClient(
            endpoint=service_url,
            credential_token_provider=self._connections.get_token_provider(
                claims_identity, service_url
            ),
            credential_resource_url=audience,
            credential_scopes=scopes,
        )

    async def create_user_token_client(
        self, claims_identity: ClaimsIdentity, use_anonymous: bool = False
    ) -> UserTokenClient:
        return UserTokenClient(
            credential=self._connections.get_token_provider(
                claims_identity, self._token_service_endpoint
            ),
            endpoint=self._token_service_endpoint,
        )

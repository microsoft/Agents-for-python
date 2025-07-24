from microsoft.agents.hosting.core import (
    Connections,
    AccessTokenProviderBase,
    AuthHandler,
    Storage,
    Authorization,
    OAuthFlow,
    MemoryStorage,
    oauth_flow,
)
from typing import Dict
from microsoft.agents.hosting.core.authorization.agent_auth_configuration import (
    AgentAuthConfiguration,
)
from microsoft.agents.hosting.core.authorization.claims_identity import ClaimsIdentity

from microsoft.agents.activity import TokenResponse

from unittest.mock import Mock, MagicMock, AsyncMock

import jwt


def create_test_auth_handler(
    name: str, obo: bool = False, title: str = None, text: str = None
):
    return AuthHandler(
        name,
        abs_oauth_connection_name=f"{name}-abs-connection",
        obo_connection_name=f"{name}-obo-connection" if obo else None,
        title=title,
        text=text,
    )


class TestingTokenProvider(AccessTokenProviderBase):
    """
    Test Token Provider for Unit Tests
    """

    def __init__(self, name: str):
        self.name = name

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return f"{self.name}-token"

    async def aquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        return f"{self.name}-obo-token"


class TestingConnectionManager(Connections):
    """
    Test Connection Manager for Unit Tests
    """

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        return TestingTokenProvider(connection_name)

    def get_default_connection(self) -> AccessTokenProviderBase:
        return TestingTokenProvider("default")

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        return self.get_default_connection()

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        return AgentAuthConfiguration()


class TestingOAuthFlow(OAuthFlow):
    """
    Test OAuthFlow for Unit Tests
    """

    def __init__(self, storage: Storage, abs_oauth_connection_name: str, **kwargs):
        super().__init__(
            storage=storage, abs_oauth_connection_name=abs_oauth_connection_name
        )


class MockOAuthFlow(Mock):
    def __init__(self, connection_name: str, token: str | None, flow_started):

        default_token = TokenResponse(
            connection_name=connection_name,
            token=f"{connection_name}-token",
        )

        if token == "default":
            token_response = default_token
        elif token:
            token_response = TokenResponse(
                connection_name=connection_name,
                token=token,
            )
        else:
            token_response = None

        super().__init__(
            get_user_token=AsyncMock(return_value=token_response),
            _get_flow_state=AsyncMock(
                return_value=oauth_flow.FlowState(flow_started=flow_started)
            ),
            begin_flow=AsyncMock(return_value=default_token),
            continue_flow=AsyncMock(return_value=default_token),
        )
        self.flow_state = None


class TestingAuthorization(Authorization):
    def __init__(
        self,
        auth_handlers: Dict[str, AuthHandler],
        token: str | None = "default",
        flow_started=False,
    ):
        storage = MemoryStorage()
        connection_manager = TestingConnectionManager()
        super().__init__(
            storage=storage,
            auth_handlers=auth_handlers,
            connection_manager=connection_manager,
        )
        for auth_handler in self._auth_handlers.values():
            auth_handler.flow = MockOAuthFlow(
                auth_handler.abs_oauth_connection_name,
                token=token,
                flow_started=flow_started,
            )

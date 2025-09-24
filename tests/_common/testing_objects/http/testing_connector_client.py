from microsft_agents.hosting.core import (
    AgentAuthConfiguration,
    AccessTokenProviderBase,
    TeamsConnectorClient,
)

from tests._common.testing_objects.http.testing_client_session import (
    TestingClientSession,
)


class TestingConnectorClient(TeamsConnectorClient):
    """Teams Connector Client for interacting with Teams-specific APIs."""

    @classmethod
    async def create_client_with_auth_async(
        cls,
        base_url: str,
        auth_config: AgentAuthConfiguration,
        auth_provider: AccessTokenProviderBase,
        scope: str,
    ) -> "TeamsConnectorClient":
        """
        Creates a new instance of TeamsConnectorClient with authentication.

        :param base_url: The base URL for the API.
        :param auth_config: The authentication configuration.
        :param auth_provider: The authentication provider.
        :param scope: The scope for the authentication token.
        :return: A new instance of TeamsConnectorClient.
        """
        session = TestingClientSession(
            base_url=base_url, headers={"Accept": "application/json"}
        )

        token = await auth_provider.get_access_token(auth_config, scope)
        if len(token) > 1:
            session.headers.update({"Authorization": f"Bearer {token}"})

        return cls(session)

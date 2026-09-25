from microsoft_agents.hosting.core import (
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)
from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential

from microsoft_agents.hosting.core.authorization._helpers import (
    _CallableTokenCredential,
)

_TEST_TOKEN_EXPIRATION = 2**31 - 1


class TestingTokenProvider(AccessTokenProviderBase):
    """
    Access token provider for unit tests.

    This test double simulates an access token provider that returns predictable
    token values based on the provider name. It implements both standard token
    acquisition and On-Behalf-Of (OBO) token flows for comprehensive testing
    of authentication scenarios.
    """

    def __init__(self, name: str):
        """
        Initialize the testing token provider.

        Args:
            name: Identifier used to generate predictable token values
        """
        self.name = name
        self._configuration = AgentAuthConfiguration()

    @property
    def configuration(self) -> AgentAuthConfiguration:
        return self._configuration

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        """
        Get an access token for the specified resource and scopes.

        Returns a predictable token string based on the provider name for testing.

        Args: (unused in test implementation)
            resource_url: URL of the resource requiring authentication
            scopes: List of OAuth scopes requested
            force_refresh: Whether to force token refresh

        Returns:
            str: Test token in format "{name}-token"
        """
        return f"{self.name}-token"

    def get_token_credential(self) -> AsyncTokenCredential:
        async def get_token(*scopes: str, **kwargs) -> AccessToken:
            return AccessToken(f"{self.name}-token", _TEST_TOKEN_EXPIRATION)

        return _CallableTokenCredential(get_token)

    async def acquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        """
        Acquire a token on behalf of another user (OBO flow).

        Returns a predictable OBO token string for testing scenarios involving
        delegated permissions and token exchange.

        Args: (unused in test implementation)
            scopes: List of OAuth scopes requested for the OBO token
            user_assertion: JWT token representing the user's identity

        Returns:
            str: Test OBO token in format "{name}-obo-token"
        """
        return f"{self.name}-obo-token"

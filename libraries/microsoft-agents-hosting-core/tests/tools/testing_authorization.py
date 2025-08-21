"""
Testing utilities for authorization functionality

This module provides mock implementations and helper classes for testing authorization,
authentication, and token management scenarios. It includes test doubles for token
providers, connection managers, and authorization handlers that can be configured
to simulate various authentication states and flow conditions.
"""

from microsoft.agents.hosting.core import (
    Connections,
    AccessTokenProviderBase,
    AuthHandler,
    Authorization,
    MemoryStorage,
    OAuthFlow,
)
from typing import Dict, Union
from microsoft.agents.hosting.core.authorization.agent_auth_configuration import (
    AgentAuthConfiguration,
)
from microsoft.agents.hosting.core.authorization.claims_identity import ClaimsIdentity

from microsoft.agents.activity import TokenResponse

from unittest.mock import Mock, AsyncMock


def create_test_auth_handler(
    name: str, obo: bool = False, title: str = None, text: str = None
):
    """
    Creates a test AuthHandler instance with standardized connection names.

    This helper function simplifies the creation of AuthHandler objects for testing
    by automatically generating connection names based on the provided name and
    optionally including On-Behalf-Of (OBO) connection configuration.

    Args:
        name: Base name for the auth handler, used to generate connection names
        obo: Whether to include On-Behalf-Of connection configuration
        title: Optional title for the auth handler
        text: Optional descriptive text for the auth handler

    Returns:
        AuthHandler: Configured auth handler instance with test-friendly connection names
    """
    return AuthHandler(
        name,
        abs_oauth_connection_name=f"{name}-abs-connection",
        obo_connection_name=f"{name}-obo-connection" if obo else None,
        title=title,
        text=text,
    )


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

    async def aquire_token_on_behalf_of(
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


class TestingConnectionManager(Connections):
    """
    Connection manager for unit tests.

    This test double provides a simplified connection management interface that
    returns TestingTokenProvider instances for all connection requests. It enables
    testing of authorization flows without requiring actual OAuth configurations
    or external authentication services.
    """

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        """
        Get a token provider for the specified connection name.

        Args:
            connection_name: Name of the OAuth connection

        Returns:
            AccessTokenProviderBase: TestingTokenProvider configured with the connection name
        """
        return TestingTokenProvider(connection_name)

    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default token provider.

        Returns:
            AccessTokenProviderBase: TestingTokenProvider configured with "default" name
        """
        return TestingTokenProvider("default")

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get a token provider based on claims identity and service URL.

        In this test implementation, returns the default connection regardless
        of the provided parameters.

        Args: (unused in test implementation)
            claims_identity: User's claims and identity information
            service_url: URL of the service requiring authentication

        Returns:
            AccessTokenProviderBase: The default TestingTokenProvider
        """
        return self.get_default_connection()

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        """
        Get the default authentication configuration.

        Returns:
            AgentAuthConfiguration: Empty configuration suitable for testing
        """
        return AgentAuthConfiguration()


class TestingAuthorization(Authorization):
    """
    Authorization system for comprehensive unit testing.

    This test double extends the Authorization class to provide a fully mocked
    authorization environment suitable for testing various authentication scenarios.
    It automatically configures auth handlers with mock OAuth flows that can simulate
    different states like successful authentication, failed sign-in, or in-progress flows.
    """

    def __init__(
        self,
        auth_handlers: Dict[str, AuthHandler],
        token: Union[str, None] = "default",
        flow_started=False,
        sign_in_failed=False,
    ):
        """
        Initialize the testing authorization system.

        Sets up a complete test authorization environment with memory storage,
        test connection manager, and configures all provided auth handlers with
        mock OAuth flows.

        Args:
            auth_handlers: Dictionary mapping handler names to AuthHandler instances
            token: Token value to use in mock responses. "default" uses auto-generated
                   tokens, None simulates no token available, or provide custom jwt token string
            flow_started: Simulate OAuth flows that have already started
            sign_in_failed: Simulate failed sign-in attempts
        """
        # Initialize with test-friendly components
        storage = MemoryStorage()
        connection_manager = TestingConnectionManager()
        super().__init__(
            storage=storage,
            auth_handlers=auth_handlers,
            connection_manager=connection_manager,
            service_url="a"
        )

        # Configure each auth handler with mock OAuth flow behavior
        for auth_handler in self._auth_handlers.values():
            # Create default token response for this auth handler
            default_token = TokenResponse(
                connection_name=auth_handler.abs_oauth_connection_name,
                token=f"{auth_handler.abs_oauth_connection_name}-token",
            )

            # Determine token response based on configuration
            if token == "default":
                token_response = default_token
            elif token:
                token_response = TokenResponse(
                    connection_name=auth_handler.abs_oauth_connection_name,
                    token=token,
                )
            else:
                token_response = None

            # Mock the OAuth flow with configurable behavior
            auth_handler.flow = Mock(
                get_user_token=AsyncMock(return_value=token_response),
                _get_flow_state=AsyncMock(
                    # sign-in failed requires flow to be started
                    return_value=oauth_flow.FlowState(
                        flow_started=(flow_started or sign_in_failed)
                    )
                ),
                begin_flow=AsyncMock(return_value=default_token),
                # Mock flow continuation with optional failure simulation
                continue_flow=AsyncMock(
                    return_value=None if sign_in_failed else default_token
                ),
            )

            auth_handler.flow.flow_state = None

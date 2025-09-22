from typing import Union

from microsoft_agents.activity import TokenResponse

from microsoft_agents.hosting.core import Authorization, AuthHandler, MemoryStorage

from .testing_connection_manager import TestingConnectionManager


# this is broken
# keeping it around for reference
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
        mocker,
        auth_handlers: dict[str, AuthHandler],
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
            service_url="a",
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
            auth_handler.flow = mocker.Mock(
                get_user_token=mocker.AsyncMock(return_value=token_response),
                _get_flow_state=mocker.AsyncMock(
                    # sign-in failed requires flow to be started
                    return_value=oauth_flow.FlowState(
                        flow_started=(flow_started or sign_in_failed)
                    )
                ),
                begin_flow=mocker.AsyncMock(return_value=default_token),
                # Mock flow continuation with optional failure simulation
                continue_flow=mocker.AsyncMock(
                    return_value=None if sign_in_failed else default_token
                ),
            )

            auth_handler.flow.flow_state = None

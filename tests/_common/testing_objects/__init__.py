from tests._common.testing_objects.mocks.mock_msal_auth import agentic_mock_class_MsalAuth
from .adapters import TestingAdapter

from .mocks import (
    MockMsalAuth,
    mock_OAuthFlow,
    mock_class_OAuthFlow,
    mock_UserTokenClient,
    mock_class_UserTokenClient,
    mock_class_UserAuthorization,
    mock_class_AgenticAuthorization,
    mock_class_Authorization,
    agentic_mock_class_MsalAuth
)

from .testing_authorization import TestingAuthorization
from .testing_connection_manager import TestingConnectionManager
from .testing_custom_state import TestingCustomState
from .testing_token_provider import TestingTokenProvider
from .testing_user_token_client import TestingUserTokenClient

__all__ = [
    "MockMsalAuth",
    "mock_OAuthFlow",
    "mock_class_OAuthFlow",
    "mock_UserTokenClient",
    "mock_class_UserTokenClient",
    "TestingAuthorization",
    "TestingConnectionManager",
    "TestingCustomState",
    "TestingTokenProvider",
    "TestingUserTokenClient",
    "TestingAdapter",
    "mock_class_UserAuthorization",
    "mock_class_AgenticAuthorization",
    "mock_class_Authorization",
    "agentic_mock_class_MsalAuth"
]

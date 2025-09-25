from microsoft_agents.hosting.core import (
    Authorization,
    UserAuthorization,
    AgenticAuthorization
)
from microsoft_agents.hosting.core.app.auth import SignInResponse

def mock_class_UserAuthorization(mocker, sign_in_return=None):
    if sign_in_return is None:
        sign_in_return = SignInResponse()
    mocker.patch(UserAuthorization, sign_in=mocker.AsyncMock(return_value=sign_in_return))

def mock_class_AgenticAuthorization(mocker, sign_in_return=None):
    if sign_in_return is None:
        sign_in_return = SignInResponse()
    mocker.patch(AgenticAuthorization, sign_in=mocker.AsyncMock(return_value=sign_in_return))

def mock_class_Authorization(mocker, start_or_continue_sign_in_return=False):
    mocker.patch(Authorization, start_or_continue_sign_in=mocker.AsyncMock(return_value=start_or_continue_sign_in_return))
from microsoft_agents.hosting.core import (
    Authorization,
    UserAuthorization,
    AgenticUserAuthorization,
    SignInResponse
)

def mock_class_UserAuthorization(mocker, sign_in_return=None):
    if sign_in_return is None:
        sign_in_return = SignInResponse()
    mocker.patch.object(UserAuthorization, "sign_in", return_value=sign_in_return)
    mocker.patch.object(UserAuthorization, "sign_out")


def mock_class_AgenticAuthorization(mocker, sign_in_return=None):
    if sign_in_return is None:
        sign_in_return = SignInResponse()
    mocker.patch.object(AgenticUserAuthorization, "sign_in", return_value=sign_in_return)
    mocker.patch.object(AgenticUserAuthorization, "sign_out")


def mock_class_Authorization(mocker, start_or_continue_sign_in_return=False):
    mocker.patch.object(
        Authorization,
        "start_or_continue_sign_in",
        return_value=start_or_continue_sign_in_return,
    )

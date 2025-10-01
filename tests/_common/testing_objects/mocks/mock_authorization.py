from microsoft_agents.activity import TokenResponse

from microsoft_agents.hosting.core import Authorization
from microsoft_agents.hosting.core.app.oauth import (
    _UserAuthorization,
    AgenticUserAuthorization,
    _SignInResponse,
)


def mock_class_UserAuthorization(
    mocker, sign_in_return=None, get_refreshed_token_return=None
):
    if sign_in_return is None:
        sign_in_return = _SignInResponse()
    if get_refreshed_token_return is None:
        get_refreshed_token_return = TokenResponse()
    mocker.patch.object(_UserAuthorization, "_sign_in", return_value=sign_in_return)
    mocker.patch.object(_UserAuthorization, "_sign_out")
    mocker.patch.object(
        _UserAuthorization,
        "get_refreshed_token",
        return_value=get_refreshed_token_return,
    )


def mock_class_AgenticUserAuthorization(
    mocker, sign_in_return=None, get_refreshed_token_return=None
):
    if sign_in_return is None:
        sign_in_return = _SignInResponse()
    if get_refreshed_token_return is None:
        get_refreshed_token_return = TokenResponse()
    mocker.patch.object(
        AgenticUserAuthorization, "_sign_in", return_value=sign_in_return
    )
    mocker.patch.object(AgenticUserAuthorization, "_sign_out")
    mocker.patch.object(
        AgenticUserAuthorization,
        "get_refreshed_token",
        return_value=get_refreshed_token_return,
    )


def mock_class_Authorization(mocker, start_or_continue_sign_in_return=False):
    mocker.patch.object(
        Authorization,
        "_start_or_continue_sign_in",
        return_value=start_or_continue_sign_in_return,
    )

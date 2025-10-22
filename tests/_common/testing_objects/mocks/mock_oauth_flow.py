from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core._oauth import _OAuthFlow

from tests._common.data import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()


def mock_OAuthFlow(
    mocker,
    get_user_token_return=DEFAULTS.token,
    begin_or_continue_flow_return=None,
    begin_flow_return=None,
    continue_flow_return=None,
):
    # mock_oauth_flow_class.get_user_token = mocker.AsyncMock(return_value=token_response)
    # mock_oauth_flow_class.sign_out = mocker.AsyncMock()
    if isinstance(get_user_token_return, str):
        get_user_token_return = TokenResponse(token=get_user_token_return)
    mocker.patch.object(
        _OAuthFlow, "get_user_token", return_value=get_user_token_return
    )
    mocker.patch.object(_OAuthFlow, "sign_out")
    mocker.patch.object(
        _OAuthFlow, "begin_or_continue_flow", return_value=begin_or_continue_flow_return
    )
    mocker.patch.object(_OAuthFlow, "begin_flow", return_value=begin_flow_return)
    mocker.patch.object(_OAuthFlow, "continue_flow", return_value=continue_flow_return)


def mock_class_OAuthFlow(
    mocker,
    get_user_token_return=DEFAULTS.token,
    begin_or_continue_flow_return=None,
    begin_flow_return=None,
    continue_flow_return=None,
):
    mocker.patch(
        "microsoft_agents.hosting.core._oauth._OAuthFlow",
        new=mock_OAuthFlow(
            mocker,
            get_user_token_return=get_user_token_return,
            begin_or_continue_flow_return=begin_or_continue_flow_return,
            begin_flow_return=begin_flow_return,
            continue_flow_return=continue_flow_return,
        ),
    )


# def patch_flow(
#     self,
#     mocker,
#     flow_response=None,
#     token=None,
# ):
#     mocker.patch.object(
#             OAuthFlow, "get_user_token", return_value=TokenResponse(token=token)
#     )
#     mocker.patch.object(OAuthFlow, "sign_out")
#     mocker.patch.object(
#             OAuthFlow, "begin_or_continue_flow", return_value=flow_response
#     )

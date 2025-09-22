from microsoft_agents.activity import (
    TokenResponse,
    SignInResource,
)
from microsoft_agents.hosting.core import UserTokenClient

from tests._common.type_defs import SKIP


def mock_UserTokenClient(
    mocker,
    get_token_return=SKIP,
    exchange_token_return=SKIP,
    get_sign_in_resource_return=SKIP,
):

    mock_user_token_client = mocker.Mock(spec=UserTokenClient)

    if get_token_return is not SKIP:
        if isinstance(get_token_return, str):
            get_token_return = TokenResponse(token=get_token_return)
        mock_user_token_client.user_token.get_token = mocker.AsyncMock(
            return_value=get_token_return
        )

    if exchange_token_return is not SKIP:
        if isinstance(exchange_token_return, str):
            exchange_token_return = TokenResponse(token=exchange_token_return)
        mock_user_token_client.user_token.exchange_token = mocker.AsyncMock(
            return_value=exchange_token_return
        )

    if get_sign_in_resource_return is not SKIP:
        mock_user_token_client.agent_sign_in.get_sign_in_resource = mocker.AsyncMock(
            return_value=get_sign_in_resource_return
        )

    mock_user_token_client.user_token.sign_out = mocker.AsyncMock(return_value=None)

    return mock_user_token_client


def mock_class_UserTokenClient(
    mocker,
    get_token_return=SKIP,
    exchange_token_return=SKIP,
    get_sign_in_resource_return=SKIP,
):
    mocker.patch(
        "UserTokenClient",
        new=mock_UserTokenClient(
            mocker,
            get_token_return=get_token_return,
            exchange_token_return=exchange_token_return,
            get_sign_in_resource_return=get_sign_in_resource_return,
        ),
    )

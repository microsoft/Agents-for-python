from ._utils import SKIP

from microsoft_agents.hosting.core import UserTokenClient

def mock_UserTokenClient(mocker, get_user_token_return=SKIP, sign_out_user_return=SKIP, token_exchange_return=SKIP):

    mock_user_token_client = mocker.Mock(spec=UserTokenClient)

    if get_user_token_return is not SKIP:
        mock_user_token_client.user_token.get_token = mocker.AsyncMock(return_value=get_user_token_return)

    if sign_out_user_return is not SKIP:
        mock_user_token_client.user_token.sign_out_user = mocker.AsyncMock(return_value=sign_out_user_return)

    if token_exchange_return is not SKIP:
        mock_user_token_client.user_token.exchange_token = mocker.AsyncMock(return_value=token_exchange_return)
    
    return mock_user_token_client

def mock_class_UserTokenClient(mocker, get_user_token_return=SKIP, sign_out_user_return=SKIP, token_exchange_return=SKIP):
    mocker.patch(
        "microsoft_agents.hosting.core.UserTokenClient",
        new=mock_UserTokenClient(
            mocker,
            get_user_token_return=get_user_token_return,
            sign_out_user_return=sign_out_user_return,
            token_exchange_return=token_exchange_return,
        ),
    )


from ._utils import SKIP

from microsoft_agents.hosting.core import UserTokenClient

def mock_UserTokenClient(mocker, get_user_token_return=SKIP, sign_out_user_return=SKIP, token_exchange_return=SKIP):

    mock_user_token_client = mocker.Mock(spec=UserTokenClient)

    if get_user_token_return is not SKIP:
        mock_user_token_client.user_token.get_token = mocker.AsyncMock(return_value=get_user_token_return)

    if sign_out_user_return is not SKIP:
        mock_user_token_client.user_token.sign_out_user = mocker.AsyncMock(return_value=sign_out_user_return)

    if token_exchange_return is not SKIP:
        mock_user_token_client.user_token.exchange_token = mocker.AsyncMock(return_value=token_exchange_return)
    
    return mock_user_token_client
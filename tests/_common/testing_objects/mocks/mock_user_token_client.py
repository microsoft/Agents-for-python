from typing import Union

from microsoft_agents.activity import (
    TokenResponse,
    SignInResource,
    TokenOrSignInResourceResponse,
)
from microsoft_agents.hosting.core import UserTokenClient

from tests._common.type_defs import SKIP


def mock_UserTokenClient(
    mocker,
    get_token_return: Union[str, TokenResponse] = SKIP,
    exchange_token_return: Union[str, TokenResponse] = SKIP,
    get_sign_in_resource_return: Union[str, SignInResource] = SKIP,
    get_token_or_sign_in_resource_return: Union[
        str, TokenResponse, SignInResource, TokenOrSignInResourceResponse
    ] = SKIP,
):

    mock_user_token_client = mocker.Mock(spec=UserTokenClient)

    async def get_user_token(user_id, connection_name, channel_id, magic_code=None):
        return await mock_user_token_client.user_token.get_token(
            user_id=user_id,
            connection_name=connection_name,
            channel_id=channel_id,
            code=magic_code,
        )

    async def sign_out_user(user_id, connection_name, channel_id):
        return await mock_user_token_client.user_token.sign_out(
            user_id=user_id,
            connection_name=connection_name,
            channel_id=channel_id,
        )

    async def exchange_token(user_id, connection_name, channel_id, exchange_request):
        return await mock_user_token_client.user_token.exchange_token(
            user_id=user_id,
            connection_name=connection_name,
            channel_id=channel_id,
            body=exchange_request.model_dump(exclude_none=True),
        )

    async def get_token_or_sign_in_resource(
        connection_name,
        activity,
        code=None,
        final_redirect=None,
        fwd_url=None,
    ):
        state = UserTokenClient._create_token_exchange_state(
            "test-app-id",
            connection_name,
            activity,
        )
        conversation = activity.get_conversation_reference(force_base_channel=True)
        return await mock_user_token_client.user_token._get_token_or_sign_in_resource(
            activity.from_property.id,
            connection_name,
            conversation.channel_id,
            state,
        )

    mock_user_token_client.get_user_token = mocker.AsyncMock(side_effect=get_user_token)
    mock_user_token_client.sign_out_user = mocker.AsyncMock(side_effect=sign_out_user)
    mock_user_token_client.exchange_token = mocker.AsyncMock(side_effect=exchange_token)
    mock_user_token_client.get_token_or_sign_in_resource = mocker.AsyncMock(
        side_effect=get_token_or_sign_in_resource
    )

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

    if get_token_or_sign_in_resource_return is not SKIP:
        if isinstance(get_token_or_sign_in_resource_return, TokenResponse):
            get_token_or_sign_in_resource_return = TokenOrSignInResourceResponse(
                token_response=get_token_or_sign_in_resource_return
            )
        elif isinstance(get_token_or_sign_in_resource_return, SignInResource):
            get_token_or_sign_in_resource_return = TokenOrSignInResourceResponse(
                sign_in_resource=get_token_or_sign_in_resource_return
            )
        mock_user_token_client.user_token._get_token_or_sign_in_resource = (
            mocker.AsyncMock(return_value=get_token_or_sign_in_resource_return)
        )

    mock_user_token_client.user_token.sign_out = mocker.AsyncMock(return_value=None)

    return mock_user_token_client


def mock_class_UserTokenClient(
    mocker,
    get_token_return: Union[str, TokenResponse] = SKIP,
    exchange_token_return: Union[str, TokenResponse] = SKIP,
    get_sign_in_resource_return: Union[str, SignInResource] = SKIP,
    get_token_or_sign_in_resource_return: Union[
        str, TokenResponse, SignInResource, TokenOrSignInResourceResponse
    ] = SKIP,
):
    mocker.patch(
        "UserTokenClient",
        new=mock_UserTokenClient(
            mocker,
            get_token_return=get_token_return,
            exchange_token_return=exchange_token_return,
            get_sign_in_resource_return=get_sign_in_resource_return,
            get_token_or_sign_in_resource_return=get_token_or_sign_in_resource_return,
        ),
    )

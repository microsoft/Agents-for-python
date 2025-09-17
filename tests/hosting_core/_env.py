class TestingUserTokenClientMixin:
    
    def UserTokenClient(mocker, get_token_return=DEFAULTS.token):

        user_token_client = mocker.Mock(spec=UserTokenClientBase)
        user_token_client.user_token = mocker.Mock(spec=UserTokenBase)
        user_token_client.user_token.get_token = mocker.AsyncMock()
        user_token_client.user_token.sign_out = mocker.AsyncMock()

        return_value = TokenResponse()
        if get_token_return:
            return_value = TokenResponse(token=get_token_return)
        user_token_client.user_token.get_token.return_value = return_value

        return user_token_client

class TestingActivityMixin:

    def Activity(
        self,
        mocker,
        activity_type=ActivityTypes.message,
        name="a",
        value=None,
        text="a",
    ):
        mock_conversation_ref = mocker.MagicMock(ConversationReference)
        mocker.patch.object(
            Activity,
            "get_conversation_reference",
            return_value=mocker.MagicMock(ConversationReference),
        )
        # mocker.patch.object(ConversationReference, "create", return_value=conv_ref())
        return Activity(
            type=activity_type,
            name=name,
            from_property=ChannelAccount(id=DEFAULTS.user_id),
            channel_id=DEFAULTS.channel_id,
            # get_conversation_reference=mocker.Mock(return_value=conv_ref),
            relates_to=mocker.MagicMock(ConversationReference),
            value=value,
            text=text,
        )
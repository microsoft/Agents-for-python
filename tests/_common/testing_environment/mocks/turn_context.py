from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

class TestingTurnContextMixin:

    def TurnContext(
        self,
        mocker,
        channel_id=DEFAULTS.channel_id,
        user_id=DEFAULTS.user_id,
        user_token_client=None,
        *args,
        **kwargs
    ):

        if not user_token_client:
            user_token_client = self.create_mock_user_token_client(mocker)

        turn_context = mocker.Mock()
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = user_id
        turn_context.activity.type = ActivityTypes.message
        turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
        turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
        agent_identity = mocker.Mock()
        agent_identity.claims = {"aud": MS_APP_ID}
        turn_context.turn_state = {
            "__user_token_client": user_token_client,
            "__agent_identity_key": agent_identity,
        }
        return turn_context

class AuthTestingTurnContextMixin(TestingTurnContextMixin):

    def TurnContext(
        self,
        mocker,
        user_token_client,
        channel_id=DEFAULTS.channel_id,
        user_id=DEFAULTS.user_id,
        *args,
        **kwargs
    ):
        turn_context = super().TurnContext(mocker, channel_id
        turn_context.turn_state["__user_token_client"] = user_token_client
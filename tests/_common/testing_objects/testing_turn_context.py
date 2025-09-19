from microsoft_agents.activity import (
    ActivityTypes
)

from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

def testing_TurnContext(
    mocker,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    user_token_client=None,
    *args,
    **kwargs
):
    turn_context = mocker.Mock()
    turn_context.activity.channel_id = channel_id
    turn_context.activity.from_property.id = user_id
    turn_context.activity.type = ActivityTypes.message
    turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
    turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.turn_state = {
        "__user_token_client": user_token_client,
        "__agent_identity_key": agent_identity,
    }
    return turn_context

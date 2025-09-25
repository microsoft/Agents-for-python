from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.hosting.core import TurnContext

from tests._common.data import TEST_DEFAULTS
from tests._common.testing_objects import mock_UserTokenClient

DEFAULTS = TEST_DEFAULTS()


def testing_Activity():
    return Activity(
        type=ActivityTypes.message,
        channel_id=DEFAULTS.channel_id,
        from_property={"id": DEFAULTS.user_id},
        text="Hello, World!",
    )


def testing_TurnContext(
    mocker,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    user_token_client=None,
    activity=None,
):
    if not user_token_client:
        user_token_client = mock_UserTokenClient(mocker)

    turn_context = mocker.Mock()
    if not activity:
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = user_id
        turn_context.activity.type = ActivityTypes.message
    else:
        turn_context.activity = activity
    turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
    turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.turn_state = {
        "__user_token_client": user_token_client,
        "__agent_identity_key": agent_identity,
    }
    return turn_context


def testing_TurnContext_magic(
    mocker,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    user_token_client=None,
    activity=None,
):
    if not user_token_client:
        user_token_client = mock_UserTokenClient(mocker)

    turn_context = mocker.MagicMock(spec=TurnContext)
    turn_context.adapter = mocker.Mock()
    if not activity:
        turn_context.activity = mocker.Mock()
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = user_id
        turn_context.activity.type = ActivityTypes.message
    else:
        turn_context.activity = activity
    turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
    turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.turn_state = mocker.Mock()
    turn_context.turn_state = {
        "__user_token_client": user_token_client,
        "__agent_identity_key": agent_identity,
    }
    return turn_context

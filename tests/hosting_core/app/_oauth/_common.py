from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.hosting.core import TurnContext, UserTokenClientBase

from tests._common.data import DEFAULT_TEST_VALUES
from tests._common.testing_objects import mock_UserTokenClient

DEFAULTS = DEFAULT_TEST_VALUES()


def create_testing_Activity():
    return Activity(
        type=ActivityTypes.message,
        channel_id=DEFAULTS.channel_id,
        from_property={"id": DEFAULTS.user_id},
        text="Hello, World!",
    )


def create_testing_TurnContext(
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
        turn_context.activity = Activity(
            type=ActivityTypes.message,
            channel_id=channel_id,
            from_property={"id": user_id},
        )
    else:
        turn_context.activity = activity
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.identity = agent_identity
    turn_context.services = mocker.Mock()
    turn_context.services.get.side_effect = lambda key: (
        user_token_client if key is UserTokenClientBase else None
    )
    turn_context.turn_state = {}
    return turn_context


def create_testing_TurnContext_magic(
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
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.identity = agent_identity
    turn_context.services = mocker.Mock()
    turn_context.services.get.side_effect = lambda key: (
        user_token_client if key is UserTokenClientBase else None
    )
    turn_context.turn_state = {}
    return turn_context

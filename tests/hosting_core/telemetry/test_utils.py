from microsoft_agents.activity import (
    Activity,
    ConversationAccount,
    DeliveryModes,
)
from microsoft_agents.hosting.core.telemetry.attributes import UNKNOWN
from microsoft_agents.hosting.core.telemetry.utils import (
    format_scopes,
    get_conversation_id,
    get_delivery_mode,
)

# ---- format_scopes ----


def test_format_scopes_single():
    assert format_scopes(["User.Read"]) == "User.Read"


def test_format_scopes_multiple():
    assert format_scopes(["User.Read", "Mail.Read"]) == "User.Read,Mail.Read"


def test_format_scopes_none():
    assert format_scopes(None) == UNKNOWN


def test_format_scopes_empty_list():
    assert format_scopes([]) == UNKNOWN


# ---- get_conversation_id ----


def test_get_conversation_id_present():
    activity = Activity(
        type="message",
        conversation=ConversationAccount(id="conv-123"),
    )
    assert get_conversation_id(activity) == "conv-123"


def test_get_conversation_id_no_conversation():
    activity = Activity(type="message")
    assert get_conversation_id(activity) == UNKNOWN


# ---- get_delivery_mode ----


def test_get_delivery_mode_enum():
    activity = Activity(
        type="message",
        delivery_mode=DeliveryModes.expect_replies,
    )
    assert get_delivery_mode(activity) == "expectReplies"


def test_get_delivery_mode_string():
    activity = Activity(type="message", delivery_mode="custom_mode")
    assert get_delivery_mode(activity) == "custom_mode"


def test_get_delivery_mode_none():
    activity = Activity(type="message")
    assert get_delivery_mode(activity) == UNKNOWN


def test_get_delivery_mode_all_enum_values():
    for mode in DeliveryModes:
        activity = Activity(type="message", delivery_mode=mode)
        assert get_delivery_mode(activity) == mode.value

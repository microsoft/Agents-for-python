from types import SimpleNamespace

from microsoft_agents.activity import Activity, ConversationAccount, ChannelAccount
from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.telemetry.turn_context.spans import (
    TurnContextSendActivities,
)
from microsoft_agents.hosting.core.telemetry.turn_context import constants

from tests._common.fixtures.telemetry import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)


def _make_context(**activity_overrides):
    defaults = dict(
        type="message",
        channel_id="msteams",
        conversation=ConversationAccount(id="conv-1"),
        from_property=ChannelAccount(id="user-1"),
        recipient=ChannelAccount(id="bot-1"),
    )
    defaults.update(activity_overrides)
    activity = Activity(**defaults)
    return SimpleNamespace(activity=activity)


# ---- TurnContextSendActivities ----


def test_send_activity_creates_span(test_exporter):
    ctx = _make_context()

    with TurnContextSendActivities(ctx):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_TURN_SEND_ACTIVITY


def test_send_activity_span_attributes(test_exporter):
    ctx = _make_context()

    with TurnContextSendActivities(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-1"


def test_send_activity_no_conversation(test_exporter):
    ctx = _make_context()
    ctx.activity.conversation = None

    with TurnContextSendActivities(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN

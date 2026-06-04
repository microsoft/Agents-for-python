# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    ConversationParameters,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.app.proactive.create_conversation_options import (
    CreateConversationOptions,
)
from microsoft_agents.hosting.core.app.proactive.telemetry import constants
from microsoft_agents.hosting.core.app.proactive.telemetry.spans import (
    ProactiveStoreConversation,
    ProactiveGetConversation,
    ProactiveDeleteConversation,
    ProactiveSendActivity,
    ProactiveContinueConversation,
    ProactiveCreateConversation,
)

from tests._common.fixtures.telemetry import (  # noqa: F401 — fixture imports
    test_telemetry,
    test_exporter,
    test_metric_reader,
)


def _make_activity(activity_type="message", channel_id="msteams"):
    return Activity(type=activity_type, channel_id=channel_id)


_MEMBERS_SENTINEL = object()


def _make_create_options(
    channel_id="msteams",
    members=_MEMBERS_SENTINEL,
    parameters_present=True,
):
    params = None
    if parameters_present:
        if members is _MEMBERS_SENTINEL:
            params = ConversationParameters()
        else:
            params = ConversationParameters(members=members)
    return CreateConversationOptions(
        identity=ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True),
        channel_id=channel_id,
        parameters=params,
        service_url="https://smba.trafficmanager.net/teams/",
    )


# ---------------------------------------------------------------------------
# ProactiveStoreConversation
# ---------------------------------------------------------------------------


def test_store_conversation_creates_span(test_exporter):
    with ProactiveStoreConversation("conv-1"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_STORE_CONVERSATION


def test_store_conversation_span_attributes(test_exporter):
    with ProactiveStoreConversation("conv-1"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-1"


def test_store_conversation_empty_id_falls_back_to_unknown(test_exporter):
    with ProactiveStoreConversation(""):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


def test_store_conversation_none_id_falls_back_to_unknown(test_exporter):
    with ProactiveStoreConversation(None):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


def test_store_conversation_records_span_even_on_exception(test_exporter):
    try:
        with ProactiveStoreConversation("conv-err"):
            raise ValueError("storage exploded")
    except ValueError:
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes[attributes.CONVERSATION_ID] == "conv-err"


# ---------------------------------------------------------------------------
# ProactiveGetConversation
# ---------------------------------------------------------------------------


def test_get_conversation_creates_span(test_exporter):
    with ProactiveGetConversation("conv-1"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_GET_CONVERSATION


def test_get_conversation_span_attributes_without_share(test_exporter):
    """When share() is never called, CONVERSATION_FOUND defaults to UNKNOWN."""
    with ProactiveGetConversation("conv-1"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-1"
    assert span.attributes[attributes.CONVERSATION_FOUND] == attributes.UNKNOWN


def test_get_conversation_share_found_true(test_exporter):
    with ProactiveGetConversation("conv-1") as span:
        span.share(True)

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_FOUND] is True


def test_get_conversation_share_found_false(test_exporter):
    """Specifically guards against the `bool if ... is not None` check:
    False must not be coerced to UNKNOWN."""
    with ProactiveGetConversation("conv-1") as span:
        span.share(False)

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_FOUND] is False


def test_get_conversation_empty_id_falls_back_to_unknown(test_exporter):
    with ProactiveGetConversation(""):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


# ---------------------------------------------------------------------------
# ProactiveDeleteConversation
# ---------------------------------------------------------------------------


def test_delete_conversation_creates_span(test_exporter):
    with ProactiveDeleteConversation("conv-1"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_DELETE_CONVERSATION


def test_delete_conversation_span_attributes(test_exporter):
    with ProactiveDeleteConversation("conv-del"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-del"


def test_delete_conversation_empty_id_falls_back_to_unknown(test_exporter):
    with ProactiveDeleteConversation(""):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


# ---------------------------------------------------------------------------
# ProactiveSendActivity
# ---------------------------------------------------------------------------


def test_send_activity_creates_span(test_exporter):
    with ProactiveSendActivity("conv-1", _make_activity()):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_SEND_ACTIVITY


def test_send_activity_span_attributes(test_exporter):
    activity = _make_activity(activity_type="message", channel_id="webchat")
    with ProactiveSendActivity("conv-1", activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-1"
    assert span.attributes[attributes.ACTIVITY_TYPE] == "message"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "webchat"


def test_send_activity_missing_activity_type_falls_back_to_unknown(test_exporter):
    # Activity model requires `type`, so use a stand-in object that exposes the
    # same attribute surface the span reads.
    activity = SimpleNamespace(type=None, channel_id="msteams")
    with ProactiveSendActivity("conv-1", activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_TYPE] == attributes.UNKNOWN


def test_send_activity_missing_channel_id_falls_back_to_unknown(test_exporter):
    activity = SimpleNamespace(type="message", channel_id=None)
    with ProactiveSendActivity("conv-1", activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == attributes.UNKNOWN


def test_send_activity_empty_conversation_id_falls_back_to_unknown(test_exporter):
    with ProactiveSendActivity("", _make_activity()):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


# ---------------------------------------------------------------------------
# ProactiveContinueConversation
# ---------------------------------------------------------------------------


def test_continue_conversation_creates_span(test_exporter):
    with ProactiveContinueConversation("conv-1", _make_activity()):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CONTINUE_CONVERSATION


def test_continue_conversation_span_attributes(test_exporter):
    activity = _make_activity(activity_type="event", channel_id="directline")
    with ProactiveContinueConversation("conv-cont", activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-cont"
    assert span.attributes[attributes.ACTIVITY_TYPE] == "event"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "directline"


def test_continue_conversation_missing_activity_fields_fall_back(test_exporter):
    activity = SimpleNamespace(type=None, channel_id=None)
    with ProactiveContinueConversation("conv-1", activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_TYPE] == attributes.UNKNOWN
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == attributes.UNKNOWN


def test_continue_conversation_records_span_even_on_exception(test_exporter):
    try:
        with ProactiveContinueConversation("conv-err", _make_activity()):
            raise RuntimeError("handler exploded")
    except RuntimeError:
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes[attributes.CONVERSATION_ID] == "conv-err"


# ---------------------------------------------------------------------------
# ProactiveCreateConversation
# ---------------------------------------------------------------------------


def test_create_conversation_creates_span(test_exporter):
    with ProactiveCreateConversation(_make_create_options()):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CREATE_CONVERSATION


def test_create_conversation_span_attributes(test_exporter):
    members = [ChannelAccount(id="u-1"), ChannelAccount(id="u-2")]
    with ProactiveCreateConversation(
        _make_create_options(channel_id="msteams", members=members)
    ):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "msteams"
    # members_count is recorded as an int when known; unknown falls back to attributes.UNKNOWN.
    assert span.attributes[attributes.MEMBERS_COUNT] == 2


def test_create_conversation_members_count_unknown_when_empty_members(test_exporter):
    """An empty list is treated the same as missing — the `and members` clause
    in ProactiveCreateConversation short-circuits to UNKNOWN."""
    with ProactiveCreateConversation(_make_create_options(members=[])):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.MEMBERS_COUNT] == attributes.UNKNOWN


def test_create_conversation_members_count_unknown_when_no_parameters(test_exporter):
    with ProactiveCreateConversation(_make_create_options(parameters_present=False)):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.MEMBERS_COUNT] == attributes.UNKNOWN


def test_create_conversation_records_span_even_on_exception(test_exporter):
    try:
        with ProactiveCreateConversation(_make_create_options()):
            raise RuntimeError("create failed")
    except RuntimeError:
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CREATE_CONVERSATION

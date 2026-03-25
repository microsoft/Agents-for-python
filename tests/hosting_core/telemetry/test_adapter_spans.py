from datetime import datetime
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry,
    SimpleSpanWrapper,
    attributes,
)
from microsoft_agents.hosting.core.telemetry.adapter.spans import (
    AdapterProcess,
    AdapterSendActivities,
    AdapterUpdateActivity,
    AdapterDeleteActivity,
    AdapterContinueConversation,
    AdapterCreateUserTokenClient,
    AdapterCreateConnectorClient,
)
from microsoft_agents.hosting.core.telemetry.adapter import constants
from microsoft_agents.activity import Activity, ConversationAccount, ChannelAccount

from tests._common.fixtures.telemetry import (  # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import (
    find_metric,
    sum_counter,
    sum_hist_count,
)


def _make_activity(**overrides) -> Activity:
    defaults = dict(
        type="message",
        id="activity-1",
        channel_id="msteams",
        text="Hello!",
        conversation=ConversationAccount(id="conversation-1"),
        from_property=ChannelAccount(id="user-1", name="User"),
        recipient=ChannelAccount(id="bot-1", name="Bot"),
    )
    defaults.update(overrides)
    return Activity(**defaults)


# ---- AdapterProcess ----


def test_adapter_process_creates_span(test_exporter):
    activity = _make_activity()

    with AdapterProcess(activity):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_PROCESS


def test_adapter_process_span_attributes(test_exporter):
    activity = _make_activity(type="invoke", channel_id="webchat")

    with AdapterProcess(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    span_attrs = dict(span.attributes)
    assert span_attrs[attributes.ACTIVITY_TYPE] == "invoke"
    assert span_attrs[attributes.ACTIVITY_CHANNEL_ID] == "webchat"
    assert attributes.CONVERSATION_ID in span_attrs
    assert attributes.ACTIVITY_DELIVERY_MODE in span_attrs
    assert attributes.IS_AGENTIC in span_attrs

def test_adapter_process_span_attributes_shared_activity(test_exporter):
    activity = _make_activity(type="invoke", channel_id="webchat")

    with AdapterProcess() as span:
        span.share(activity)

    span = test_exporter.get_finished_spans()[0]
    span_attrs = dict(span.attributes)
    assert span_attrs[attributes.ACTIVITY_TYPE] == "invoke"
    assert span_attrs[attributes.ACTIVITY_CHANNEL_ID] == "webchat"
    assert attributes.CONVERSATION_ID in span_attrs
    assert attributes.ACTIVITY_DELIVERY_MODE in span_attrs
    assert attributes.IS_AGENTIC in span_attrs


def test_adapter_process_records_metrics(test_exporter, test_metric_reader):
    activity = _make_activity()

    with AdapterProcess(activity):
        pass

    metric_data = test_metric_reader.get_metrics_data()

    received = sum_counter(
        find_metric(metric_data, constants.METRIC_ACTIVITIES_RECEIVED)
    )

    assert received == 1

    duration_count = sum_hist_count(
        find_metric(metric_data, constants.METRIC_ADAPTER_PROCESS_DURATION)
    )
    assert duration_count == 1


# ---- AdapterSendActivities ----


def test_adapter_send_activities_creates_span(test_exporter):
    activities = [_make_activity(), _make_activity(type="typing")]

    with AdapterSendActivities(activities):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_SEND_ACTIVITIES


def test_adapter_send_activities_span_attributes(test_exporter):
    activities = [_make_activity(), _make_activity()]

    with AdapterSendActivities(activities):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_COUNT] == 2
    assert span.attributes[attributes.CONVERSATION_ID] == "conversation-1"


def test_adapter_send_activities_empty_list(test_exporter):
    with AdapterSendActivities([]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_COUNT] == 0
    assert span.attributes[attributes.CONVERSATION_ID] == attributes.UNKNOWN


def test_adapter_send_activities_records_metrics(test_exporter, test_metric_reader):
    activities = [
        _make_activity(channel_id="msteams"),
        _make_activity(channel_id="webchat"),
    ]

    with AdapterSendActivities(activities):
        pass

    metric_data = test_metric_reader.get_metrics_data()
    sent = sum_counter(find_metric(metric_data, constants.METRIC_ACTIVITIES_SENT))
    assert sent == 2


# ---- AdapterUpdateActivity ----


def test_adapter_update_activity_creates_span(test_exporter):
    activity = _make_activity(id="act-42")

    with AdapterUpdateActivity(activity):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_UPDATE_ACTIVITY


def test_adapter_update_activity_span_attributes(test_exporter):
    activity = _make_activity(id="act-42")

    with AdapterUpdateActivity(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_ID] == "act-42"
    assert span.attributes[attributes.CONVERSATION_ID] == "conversation-1"


def test_adapter_update_activity_records_metrics(test_exporter, test_metric_reader):
    activity = _make_activity()

    with AdapterUpdateActivity(activity):
        pass

    metric_data = test_metric_reader.get_metrics_data()
    updated = sum_counter(find_metric(metric_data, constants.METRIC_ACTIVITIES_UPDATED))
    assert updated == 1


def test_adapter_update_activity_missing_id(test_exporter):
    activity = _make_activity(id=None)

    with AdapterUpdateActivity(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_ID] == attributes.UNKNOWN


# ---- AdapterDeleteActivity ----


def test_adapter_delete_activity_creates_span(test_exporter):
    activity = _make_activity(id="act-99")

    with AdapterDeleteActivity(activity):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_DELETE_ACTIVITY


def test_adapter_delete_activity_span_attributes(test_exporter):
    activity = _make_activity(id="act-99")

    with AdapterDeleteActivity(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_ID] == "act-99"
    assert span.attributes[attributes.CONVERSATION_ID] == "conversation-1"


def test_adapter_delete_activity_records_metrics(test_exporter, test_metric_reader):
    activity = _make_activity()

    with AdapterDeleteActivity(activity):
        pass

    metric_data = test_metric_reader.get_metrics_data()
    deleted = sum_counter(find_metric(metric_data, constants.METRIC_ACTIVITIES_DELETED))
    assert deleted == 1


# ---- AdapterContinueConversation ----


def test_adapter_continue_conversation_creates_span(test_exporter):
    activity = _make_activity()

    with AdapterContinueConversation(activity):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CONTINUE_CONVERSATION


def test_adapter_continue_conversation_span_attributes(test_exporter):
    activity = _make_activity()

    with AdapterContinueConversation(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.APP_ID] == "bot-1"
    assert span.attributes[attributes.CONVERSATION_ID] == "conversation-1"


def test_adapter_continue_conversation_no_recipient(test_exporter):
    activity = _make_activity()
    activity.recipient = None

    with AdapterContinueConversation(activity):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.APP_ID] == attributes.UNKNOWN


# ---- AdapterCreateUserTokenClient ----


def test_adapter_create_user_token_client_creates_span(test_exporter):
    with AdapterCreateUserTokenClient("https://token.example.com", ["scope1"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CREATE_USER_TOKEN_CLIENT


def test_adapter_create_user_token_client_span_attributes(test_exporter):
    with AdapterCreateUserTokenClient(
        "https://token.example.com", ["User.Read", "Mail.Read"]
    ):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert (
        span.attributes[attributes.TOKEN_SERVICE_ENDPOINT]
        == "https://token.example.com"
    )
    assert span.attributes[attributes.AUTH_SCOPES] == "User.Read,Mail.Read"


def test_adapter_create_user_token_client_no_scopes(test_exporter):
    with AdapterCreateUserTokenClient("https://token.example.com", None):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_SCOPES] == attributes.UNKNOWN


# ---- AdapterCreateConnectorClient ----


def test_adapter_create_connector_client_creates_span(test_exporter):
    with AdapterCreateConnectorClient("https://service.example.com", ["scope1"], False):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_CREATE_CONNECTOR_CLIENT


def test_adapter_create_connector_client_span_attributes(test_exporter):
    with AdapterCreateConnectorClient(
        "https://service.example.com", ["Bot.Read"], True
    ):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.SERVICE_URL] == "https://service.example.com"
    assert span.attributes[attributes.AUTH_SCOPES] == "Bot.Read"
    assert span.attributes[attributes.IS_AGENTIC] is True


def test_adapter_create_connector_client_not_agentic(test_exporter):
    with AdapterCreateConnectorClient("https://svc.example.com", None, False):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.IS_AGENTIC] is False
    assert span.attributes[attributes.AUTH_SCOPES] == attributes.UNKNOWN

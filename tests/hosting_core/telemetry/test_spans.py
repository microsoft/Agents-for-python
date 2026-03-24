from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry,
    SimpleSpanWrapper,
)

from tests._common.fixtures.telemetry import ( # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
    clear
)
from tests._common.telemetry_utils import (
    _find_metric,
    _sum_counter,
    _sum_hist_count,
)

def _build_turn_context(mocker):
    activity = SimpleNamespace(
        type="message",
        id="activity-1",
        from_property=SimpleNamespace(id="user-1"),
        recipient=SimpleNamespace(id="bot-1"),
        conversation=SimpleNamespace(id="conversation-1"),
        channel_id="msteams",
        text="Hello!",
    )
    activity.is_agentic_request = lambda: False

    context = mocker.Mock(spec=TurnContext)
    context.activity = activity
    return context

def test_start_as_current_span(mocker, test_exporter):
    """Test start_as_current_span creates a span with context attributes."""
    context = _build_turn_context(mocker)

    with agents_telemetry.start_as_current_span("test_span", context):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "test_span"

    attributes = spans[0].attributes
    assert attributes["activity.type"] == "message"
    assert attributes["agent.is_agentic"] is False
    assert attributes["from.id"] == "user-1"
    assert attributes["recipient.id"] == "bot-1"
    assert attributes["conversation.id"] == "conversation-1"
    assert attributes["channel_id"] == "msteams"
    assert attributes["message.text.length"] == 6

def test_start_timed_span(mocker, test_exporter):
    """Test start_timed_span records success status and callback payload."""
    context = _build_turn_context(mocker)
    callback = mocker.Mock()

    with agents_telemetry.start_timed_span(
        "test_timed_span",
        context,
        callback=callback,
    ):
        pass

    finished_spans = test_exporter.get_finished_spans()
    assert len(finished_spans) == 1

    finished_span = finished_spans[0]
    assert finished_span.name == "test_timed_span"
    assert finished_span.status.status_code == trace.StatusCode.OK

    completion_events = [
        event for event in finished_span.events if event.name == "test_timed_span completed"
    ]
    assert len(completion_events) == 1
    assert completion_events[0].attributes["duration_ms"] >= 0

    callback.assert_called_once()
    callback_span, duration_ms, callback_exception = callback.call_args.args
    assert callback_span.name == "test_timed_span"
    assert duration_ms >= 0
    assert callback_exception is None


def test_start_span_app_on_turn(mocker, test_exporter, test_metric_reader):
    """Test agent_turn_operation records span and turn metrics."""
    context = _build_turn_context(mocker)

    with _spans.start_span_app_on_turn(context):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == core.SPAN_APP_ON_TURN

    metric_data = test_metric_reader.get_metrics_data()
    turn_total = _sum_counter(_find_metric(metric_data, core.METRIC_TURN_TOTAL))
    turn_duration_count = _sum_hist_count(
        _find_metric(metric_data, core.METRIC_TURN_DURATION)
    )

    assert turn_total == 1
    assert turn_duration_count == 1

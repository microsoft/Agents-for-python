import pytest
from types import SimpleNamespace

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry,
    constants,
    spans as _spans,
)

@pytest.fixture(scope="module")
def test_telemetry():
    """Set up fresh in-memory exporter for testing."""
    exporter = InMemorySpanExporter()
    metric_reader = InMemoryMetricReader()

    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider([metric_reader])

    metrics.set_meter_provider(meter_provider)

    yield exporter, metric_reader

    exporter.clear()
    tracer_provider.shutdown()
    meter_provider.shutdown()

@pytest.fixture(scope="function")
def test_exporter(test_telemetry):
    """Provide the in-memory span exporter for each test."""
    exporter, _ = test_telemetry
    return exporter

@pytest.fixture(scope="function")
def test_metric_reader(test_telemetry):
    """Provide the in-memory metric reader for each test."""
    _, metric_reader = test_telemetry
    return metric_reader

@pytest.fixture(autouse=True, scope="function")
def clear(test_exporter, test_metric_reader):
    """Clear spans before each test to ensure test isolation."""
    test_exporter.clear()
    test_metric_reader.force_flush()


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


def _find_metric(metrics_data, metric_name):
    for resource_metric in metrics_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == metric_name:
                    return metric
    return None


def _sum_counter(metric, attribute_filter=None):
    if metric is None:
        return 0
    total = 0
    for point in metric.data.data_points:
        if attribute_filter is None or all(
            point.attributes.get(key) == value
            for key, value in attribute_filter.items()
        ):
            total += point.value
    return total


def _sum_hist_count(metric, attribute_filter=None):
    if metric is None:
        return 0
    total = 0
    for point in metric.data.data_points:
        if attribute_filter is None or all(
            point.attributes.get(key) == value
            for key, value in attribute_filter.items()
        ):
            total += point.count
    return total


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
    assert spans[0].name == constants.SPAN_APP_RUN

    metric_data = test_metric_reader.get_metrics_data()
    turn_total = _sum_counter(_find_metric(metric_data, constants.METRIC_TURN_TOTAL))
    turn_duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.METRIC_TURN_DURATION)
    )

    assert turn_total == 1
    assert turn_duration_count == 1

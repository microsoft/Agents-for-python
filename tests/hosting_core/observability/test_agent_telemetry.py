import pytest
from types import SimpleNamespace

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from microsoft_agents.hosting.core.observability import (
    agent_telemetry,
    constants,
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


def _build_turn_context():
    activity = SimpleNamespace(
        type="message",
        from_property=SimpleNamespace(id="user-1"),
        recipient=SimpleNamespace(id="bot-1"),
        conversation=SimpleNamespace(id="conversation-1"),
        channel_id="msteams",
        text="Hello!",
    )
    activity.is_agentic_request = lambda: False
    return SimpleNamespace(activity=activity)


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


def test_start_as_current_span(test_exporter):
    """Test start_as_current_span creates a span with context attributes."""
    context = _build_turn_context()

    with agent_telemetry.start_as_current_span("test_span", context):
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


def test_agent_turn_operation(test_exporter, test_metric_reader):
    """Test agent_turn_operation records span and turn metrics."""
    context = _build_turn_context()

    with agent_telemetry.instrument_agent_turn(context):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AGENT_TURN_OPERATION_NAME

    metric_data = test_metric_reader.get_metrics_data()
    turn_total = _sum_counter(_find_metric(metric_data, constants.AGENT_TURN_TOTAL_METRIC_NAME))
    turn_duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.AGENT_TURN_DURATION_METRIC_NAME)
    )

    assert turn_total == 1
    assert turn_duration_count == 1


def test_instrument_adapter_process(test_exporter, test_metric_reader):
    """Test instrument_adapter_process records span and duration metric."""

    with agent_telemetry.instrument_adapter_process():
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.ADAPTER_PROCESS_OPERATION_NAME

    metric_data = test_metric_reader.get_metrics_data()
    duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.ADAPTER_PROCESS_DURATION_METRIC_NAME)
    )

    assert duration_count == 1


def test_instrument_storage_op(test_exporter, test_metric_reader):
    """Test instrument_storage_op records span and operation-tagged metrics."""
    op_filter = {"operation": "read"}

    with agent_telemetry.instrument_storage_op("read"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.STORAGE_OPERATION_NAME_FORMAT.format(operation_name="read")

    metric_data = test_metric_reader.get_metrics_data()
    total = _sum_counter(
        _find_metric(metric_data, constants.STORAGE_OPERATION_TOTAL_METRIC_NAME),
        attribute_filter=op_filter,
    )
    duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.STORAGE_OPERATION_DURATION_METRIC_NAME),
        attribute_filter=op_filter,
    )

    assert total == 1
    assert duration_count == 1

def test_instrument_connector_op(test_exporter, test_metric_reader):
    """Test instrument_connector_op records span and connector-tagged metrics."""
    connector_filter = {"operation": "test_connector"}

    with agent_telemetry.instrument_connector_op("test_connector"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.CONNECTOR_REQUEST_OPERATION_NAME_FORMAT.format(operation_name="test_connector")

    metric_data = test_metric_reader.get_metrics_data()
    total = _sum_counter(
        _find_metric(metric_data, constants.CONNECTOR_REQUEST_TOTAL_METRIC_NAME),
        attribute_filter=connector_filter,
    )
    duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.CONNECTOR_REQUEST_DURATION_METRIC_NAME),
        attribute_filter=connector_filter,
    )

    assert total == 1
    assert duration_count == 1

def test_instrument_auth_token_request(test_exporter, test_metric_reader):
    """Test instrument_auth_token_request records span and auth token request metrics."""

    with agent_telemetry.instrument_auth_token_request():
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AUTH_TOKEN_REQUEST_OPERATION_NAME

    metric_data = test_metric_reader.get_metrics_data()
    total = _sum_counter(
        _find_metric(metric_data, constants.AUTH_TOKEN_REQUEST_TOTAL_METRIC_NAME)
    )
    duration_count = _sum_hist_count(
        _find_metric(metric_data, constants.AUTH_TOKEN_REQUEST_DURATION_METRIC_NAME)
    )

    assert total == 1
    assert duration_count == 1
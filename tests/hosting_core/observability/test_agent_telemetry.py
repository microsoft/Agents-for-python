import pytest
from types import SimpleNamespace

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from microsoft_agents.hosting.core.observability import agent_telemetry

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

    metrics_before = test_metric_reader.get_metrics_data()
    before_turn_total = _sum_counter(_find_metric(metrics_before, "app.turn.total"))
    before_turn_duration_count = _sum_hist_count(
        _find_metric(metrics_before, "app.turn.duration")
    )

    with agent_telemetry.agent_turn_operation(context):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "agent turn"

    metrics_after = test_metric_reader.get_metrics_data()
    after_turn_total = _sum_counter(_find_metric(metrics_after, "app.turn.total"))
    after_turn_duration_count = _sum_hist_count(
        _find_metric(metrics_after, "app.turn.duration")
    )

    assert after_turn_total == before_turn_total + 1
    assert after_turn_duration_count == before_turn_duration_count + 1


def test_adapter_process_operation(test_exporter, test_metric_reader):
    """Test adapter_process_operation records span and duration metric."""
    metrics_before = test_metric_reader.get_metrics_data()
    before_duration_count = _sum_hist_count(
        _find_metric(metrics_before, "agents.adapter.process.duration")
    )

    with agent_telemetry.adapter_process_operation():
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "adapter process"

    metrics_after = test_metric_reader.get_metrics_data()
    after_duration_count = _sum_hist_count(
        _find_metric(metrics_after, "agents.adapter.process.duration")
    )

    assert after_duration_count == before_duration_count + 1


def test_storage_operation(test_exporter, test_metric_reader):
    """Test storage_operation records span and operation-tagged metrics."""
    op_filter = {"operation": "read"}

    metrics_before = test_metric_reader.get_metrics_data()
    before_total = _sum_counter(
        _find_metric(metrics_before, "storage.operation.total"),
        attribute_filter=op_filter,
    )
    before_duration_count = _sum_hist_count(
        _find_metric(metrics_before, "storage.operation.duration"),
        attribute_filter=op_filter,
    )

    with agent_telemetry.storage_operation("read"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "storage read"

    metrics_after = test_metric_reader.get_metrics_data()
    after_total = _sum_counter(
        _find_metric(metrics_after, "storage.operation.total"),
        attribute_filter=op_filter,
    )
    after_duration_count = _sum_hist_count(
        _find_metric(metrics_after, "storage.operation.duration"),
        attribute_filter=op_filter,
    )

    assert after_total == before_total + 1
    assert after_duration_count == before_duration_count + 1
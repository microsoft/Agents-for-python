import pytest

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

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
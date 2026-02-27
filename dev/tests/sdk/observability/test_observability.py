import pytest

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from ...scenarios import load_scenario

_SCENARIO = load_scenario("quickstart", use_jwt_middleware=False)

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

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_basic(test_exporter, agent_client):
    """Test that spans are created for a simple scenario."""

    await agent_client.send_expect_replies("Hello!")
     
    spans = test_exporter.get_finished_spans()

    # We should have a span for the overall turn
    assert any(
        span.name == "agent turn"
        for span in spans
    )
    turn_span = next(span for span in spans if span.name == "agent turn")
    assert (
        "activity.type" in turn_span.attributes and
        "agent.is_agentic" in turn_span.attributes and
        "from.id" in turn_span.attributes and
        "recipient.id" in turn_span.attributes and
        "conversation.id" in turn_span.attributes and
        "channel_id" in turn_span.attributes and
        "message.text.length" in turn_span.attributes
    )
    assert turn_span.attributes["activity.type"] == "message"
    assert turn_span.attributes["agent.is_agentic"] == False
    assert turn_span.attributes["message.text.length"] == len("Hello!")

    # adapter processing is a key part of the turn, so we should have a span for it
    assert any(
        span.name == "adapter process"
        for span in spans
    )

    # storage is read when accessing conversation state
    assert any(
        span.name == "storage read"
        for span in spans
    )

    assert len(spans) >= 3

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_multiple_users(test_exporter, agent_client):
    """Test that spans are created correctly for multiple users."""

    activity1 = agent_client.template.create({
        "from.id": "user1",
        "text": "Hello from user 1"
    })

    activity2 = agent_client.template.create({
        "from.id": "user2",
        "text": "Hello from user 2"
    })

    await agent_client.send_expect_replies(activity1)
    await agent_client.send_expect_replies(activity2)

    spans = test_exporter.get_finished_spans()

    def assert_span_for_user(user_id: str):
        assert any(
            span.name == "agent turn" and span.attributes.get("from.id") == user_id
            for span in spans
        )

    assert_span_for_user("user1")
    assert_span_for_user("user2")
    
    assert len(list(filter(lambda span: span.name == "agent turn", spans))) == 2
    assert len(list(filter(lambda span: span.name == "adapter process", spans))) == 2

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_metrics(test_metric_reader, agent_client):
    """Test that metrics are recorded for a simple scenario."""

    await agent_client.send_expect_replies("Hello!")

    metrics_data = test_metric_reader.get_metrics_data()

    metrics = metrics_data.resource_metrics

    assert len(metrics) > 0
import pytest

from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ...scenarios import load_scenario

_SCENARIO = load_scenario("quickstart", use_jwt_middleware=False)

@pytest.fixture
def test_exporter():
    """Set up fresh in-memory exporter for testing."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    yield exporter

    exporter.clear()
    provider.shutdown()

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_basic(test_exporter, agent_client):
    """Test that spans are created for a simple scenario."""

    await agent_client.send_expect_replies("Hello!")
     
    spans = test_exporter.get_finished_spans()

    breakpoint()

    assert len(spans) > 0
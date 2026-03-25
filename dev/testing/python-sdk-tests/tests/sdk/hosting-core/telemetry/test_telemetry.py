import pytest

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from microsoft_agents.hosting.core.telemetry import (
    attributes,
    SERVICE_NAME,
    SERVICE_VERSION
)
from microsoft_agents.hosting.core.telemetry.adapter import constants as adapter_constants
from microsoft_agents.hosting.core.telemetry.turn_context import constants as turn_context_constants
from microsoft_agents.hosting.core.app.telemetry import constants as app_constants
from microsoft_agents.hosting.core.app.oauth.telemetry import constants as oauth_constants
from microsoft_agents.hosting.core.authorization.telemetry import constants as auth_constants
from microsoft_agents.hosting.core.connector.telemetry import constants as connector_constants
from microsoft_agents.hosting.core.storage.telemetry import constants as storage_constants

from tests.scenarios import load_scenario

from ._fixtures import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from ._utils import (
    sum_counter,
    sum_hist_count,
    find_metric
)

_SCENARIO = load_scenario("quickstart", use_jwt_middleware=False)

def get_span(spans, name):
    for span in spans:
        if span.name == name:
            return span
    return None

def assert_span(spans, name, expected_attributes: dict | None = None):
    if not expected_attributes:
        expected_attributes = {}
    span = get_span(spans, name)
    assert span is not None, f"Span '{name}' not found"
    for key, value in expected_attributes.items():
        assert key in span.attributes, f"Attribute '{key}' not found in span '{name}'"
        assert span.attributes[key] == value, f"Attribute '{key}' in span '{name}' has value '{span.attributes[key]}', expected '{value}'"

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_basic(test_exporter, agent_client):
    """Test that spans are created for a simple scenario."""

    await agent_client.send_expect_replies("Hello!")
     
    spans = test_exporter.get_finished_spans()

    # We should have a span for the overall turn
    turn_span = get_span(spans, app_constants.SPAN_ON_TURN)
    assert turn_span is not None, "Turn span not found"
    assert turn_span.attributes["activity.type"] == "message"
    assert turn_span.attributes["agent.is_agentic"] == False
    assert turn_span.attributes["message.text.length"] == len("Hello!")

    assert_span(spans, adapter_constants.SPAN_PROCESS)

    assert len(spans) >= 2

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
        assert_span(spans, app_constants.SPAN_ON_TURN, {"from.id": user_id})

    assert_span_for_user("user1")
    assert_span_for_user("user2")
    
    assert len(list(filter(lambda span: span.name == app_constants.SPAN_ON_TURN, spans))) == 2
    assert len(list(filter(lambda span: span.name == adapter_constants.SPAN_PROCESS, spans))) == 2

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_metrics(test_metric_reader, agent_client):
    """Test that metrics are recorded for a simple scenario."""

    await agent_client.send_expect_replies("Hello!")

    metrics_data = test_metric_reader.get_metrics_data()

    metrics = metrics_data.resource_metrics

    assert len(metrics) > 0
import pytest

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from microsoft_agents.activity import DeliveryModes
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

from tests.utils.telemetry_fixtures import ( # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests.utils.telemetry_utils import (
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

    for span in spans:
        if span.name == name:
            match = True
            for key, value in expected_attributes.items():
                if key not in span.attributes or span.attributes[key] != value:
                    match = False
                    break
            if match:
                return
    assert False, f"Span '{name}' with attributes {expected_attributes} not found"

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_basic(test_exporter, test_metric_reader, agent_client):
    """Test that spans are created for a simple scenario."""

    activity_id = "test-activity-id"
    activity = agent_client.template.create(
        {
            "type": "message",
            "id": activity_id
        }
    )

    await agent_client.send_expect_replies(activity)
     
    spans = test_exporter.get_finished_spans()

    # We should have a span for the overall turn
    assert_span(spans, app_constants.SPAN_ON_TURN, {
        attributes.ROUTE_AUTHORIZED: True,
        attributes.ROUTE_MATCHED: True,
        attributes.ACTIVITY_ID: activity_id,
        attributes.ACTIVITY_TYPE: "message"
    })

    assert_span(spans, app_constants.SPAN_BEFORE_TURN)
    assert_span(spans, app_constants.SPAN_AFTER_TURN)

    assert_span(spans, app_constants.SPAN_ROUTE_HANDLER, {
        attributes.ROUTE_IS_INVOKE: False,
        attributes.ROUTE_IS_AGENTIC: False,
    })

    assert_span(spans, adapter_constants.SPAN_PROCESS, {
        attributes.ACTIVITY_TYPE: "message",
        attributes.ACTIVITY_CHANNEL_ID: activity.channel_id,
        attributes.ACTIVITY_DELIVERY_MODE: DeliveryModes.expect_replies,
        attributes.CONVERSATION_ID: activity.conversation.id,
        attributes.IS_AGENTIC: False,
    })

    assert get_span(spans, adapter_constants.SPAN_CREATE_CONNECTOR_CLIENT) is None
    assert_span(spans, adapter_constants.SPAN_CREATE_USER_TOKEN_CLIENT)

    metrics_data = test_metric_reader.get_metrics_data()

    received_activities = sum_counter(find_metric(metrics_data, adapter_constants.METRIC_ACTIVITIES_RECEIVED))
    assert received_activities >= 1

    sent_activities = sum_counter(find_metric(metrics_data, adapter_constants.METRIC_ACTIVITIES_SENT))
    assert sent_activities >= 1

    process_duration_count = sum_hist_count(find_metric(metrics_data, adapter_constants.METRIC_ADAPTER_PROCESS_DURATION))
    assert process_duration_count == 1

    connector_request_count = sum_counter(find_metric(metrics_data, connector_constants.METRIC_CONNECTOR_REQUEST_COUNT))
    assert connector_request_count == 0

    user_token_client_request_count = sum_counter(find_metric(metrics_data, connector_constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
    assert user_token_client_request_count == 0

    turn_count = sum_counter(find_metric(metrics_data, app_constants.METRIC_TURN_COUNT))
    assert turn_count >= 1

    turn_errors = sum_counter(find_metric(metrics_data, app_constants.METRIC_TURN_ERROR_COUNT))
    assert turn_errors == 0

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
    
    assert len(list(filter(lambda span: span.name == app_constants.SPAN_ON_TURN, spans))) == 2
    assert len(list(filter(lambda span: span.name == adapter_constants.SPAN_PROCESS, spans))) == 2
import os

from opentelemetry.sdk.resources import Resource

# Telemetry resource information

SERVICE_NAME = "microsoft_agents"
SERVICE_VERSION = "1.0.0"

RESOURCE = Resource.create(
    {
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "telemetry.sdk.language": "python",
    }
)

# Span operation names

ADAPTER_PROCESS_OPERATION_NAME = "adapter process"
AGENT_TURN_OPERATION_NAME = "agent turn"
AUTH_TOKEN_REQUEST_OPERATION_NAME = "auth token request"
CONNECTOR_REQUEST_OPERATION_NAME_FORMAT = "connector {operation_name}"
STORAGE_OPERATION_NAME_FORMAT = "storage {operation_name}"

# Metric names

ADAPTER_PROCESS_DURATION_METRIC_NAME = "agents.adapter.process.duration"
ADAPTER_PROCESS_TOTAL_METRIC_NAME = "agents.adapter.process.total"

AGENT_TURN_DURATION_METRIC_NAME = "agents.turn.duration"
AGENT_TURN_TOTAL_METRIC_NAME = "agents.turn.total"
AGENT_TURN_ERRORS_METRIC_NAME = "agents.turn.errors"

AUTH_TOKEN_REQUEST_DURATION_METRIC_NAME = "agents.auth.request.duration"
AUTH_TOKEN_REQUEST_TOTAL_METRIC_NAME = "agents.auth.request.total"

CONNECTOR_REQUEST_TOTAL_METRIC_NAME = "agents.connector.request.total"
CONNECTOR_REQUEST_DURATION_METRIC_NAME = "agents.connector.request.duration"

STORAGE_OPERATION_DURATION_METRIC_NAME = "storage.operation.duration"
STORAGE_OPERATION_TOTAL_METRIC_NAME = "storage.operation.total"
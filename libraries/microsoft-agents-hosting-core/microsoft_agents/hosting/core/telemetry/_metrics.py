from . import constants
from ._agents_telemetry import agents_telemetry

STORAGE_OPERATIONS = agents_telemetry.meter.create_counter(
    constants.METRIC_STORAGE_OPERATION_TOTAL,
    "operation",
    description="Number of storage operations performed by the agent",
)
STORAGE_OPERATIONS_DURATION = agents_telemetry.meter.create_histogram(
    constants.METRIC_STORAGE_OPERATION_DURATION,
    "ms",
    description="Duration of storage operations in milliseconds",
)

# AgentApplication

TURN_TOTAL = agents_telemetry.meter.create_counter(
    constants.METRIC_TURN_TOTAL,
    "turn",
    description="Total number of turns processed by the agent",
)

TURN_ERRORS = agents_telemetry.meter.create_counter(
    constants.METRIC_TURN_ERRORS,
    "turn",
    description="Number of turns that resulted in an error",
)

TURN_DURATION = agents_telemetry.meter.create_histogram(
    constants.METRIC_TURN_DURATION,
    "ms",
    description="Duration of agent turns in milliseconds",
)

# Adapters

ADAPTER_PROCESS_DURATION = agents_telemetry.meter.create_histogram(
    constants.METRIC_ADAPTER_PROCESS_DURATION,
    "ms",
    description="Duration of adapter processing in milliseconds",
)

# Connectors

CONNECTOR_REQUEST_TOTAL = agents_telemetry.meter.create_counter(
    constants.METRIC_CONNECTOR_REQUEST_TOTAL,
    "request",
    description="Total number of connector requests made by the agent",
)

CONNECTOR_REQUEST_DURATION = agents_telemetry.meter.create_histogram(
    constants.METRIC_CONNECTOR_REQUEST_DURATION,
    "ms",
    description="Duration of connector requests in milliseconds",
)
from . import core
from .core._agents_telemetry import agents_telemetry

storage_operation_total = agents_telemetry.meter.create_counter(
    core.METRIC_STORAGE_OPERATION_TOTAL,
    "operation",
    description="Number of storage operations performed by the agent",
)
storage_operation_duration = agents_telemetry.meter.create_histogram(
    core.METRIC_STORAGE_OPERATION_DURATION,
    "ms",
    description="Duration of storage operations in milliseconds",
)

# AgentApplication

turn_total = agents_telemetry.meter.create_counter(
    core.METRIC_TURN_TOTAL,
    "turn",
    description="Total number of turns processed by the agent",
)

turn_errors = agents_telemetry.meter.create_counter(
    core.METRIC_TURN_ERRORS,
    "turn",
    description="Number of turns that resulted in an error",
)

turn_duration = agents_telemetry.meter.create_histogram(
    core.METRIC_TURN_DURATION,
    "ms",
    description="Duration of agent turns in milliseconds",
)

# Adapters

adapter_process_duration = agents_telemetry.meter.create_histogram(
    core.METRIC_ADAPTER_PROCESS_DURATION,
    "ms",
    description="Duration of adapter processing in milliseconds",
)

# Connectors

connector_request_total = agents_telemetry.meter.create_counter(
    core.METRIC_CONNECTOR_REQUESTS_TOTAL,
    "request",
    description="Total number of connector requests made by the agent",
)

connector_request_duration = agents_telemetry.meter.create_histogram(
    core.METRIC_CONNECTOR_REQUEST_DURATION,
    "ms",
    description="Duration of connector requests in milliseconds",
)

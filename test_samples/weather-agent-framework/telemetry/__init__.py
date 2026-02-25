# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Telemetry package for the Python Weather Agent.

Python port of sample-agent/telemetry (AgentMetrics.cs, A365OtelWrapper.cs,
AgentOTELExtensions.cs).

Typical usage in app.py::

    from telemetry import configure_opentelemetry, setup_health_routes
    from telemetry import create_aiohttp_tracing_middleware
    from telemetry import invoke_observed_agent_operation_with_context

    # 1. Configure providers once at startup (before any span/metric activity)
    configure_opentelemetry(app_name="WeatherAgent", environment="development")

    # 2. Add tracing middleware to the aiohttp app
    app = web.Application(middlewares=[create_aiohttp_tracing_middleware()])

    # 3. Register /health and /alive endpoints (development only)
    setup_health_routes(app, development=True)

    # 4. Wrap message handlers with observed operations
    await invoke_observed_agent_operation_with_context(
        "OnMessageActivity", turn_context, turn_state, handler_func
    )
"""

from .a365_otel_wrapper import invoke_observed_agent_operation_with_context
from .agent_metrics import (
    SOURCE_NAME,
    active_conversations,
    finalize_message_handling_span,
    initialize_message_handling_span,
    invoke_observed_agent_operation,
    invoke_observed_http_operation,
    message_processed_counter,
    message_processing_duration,
    meter,
    route_executed_counter,
    route_execution_duration,
    tracer,
)
from .agent_otel_extensions import (
    configure_opentelemetry,
    create_aiohttp_tracing_middleware,
    setup_health_routes,
)

__all__ = [
    # agent_metrics
    "SOURCE_NAME",
    "tracer",
    "meter",
    "message_processed_counter",
    "route_executed_counter",
    "message_processing_duration",
    "route_execution_duration",
    "active_conversations",
    "initialize_message_handling_span",
    "finalize_message_handling_span",
    "invoke_observed_http_operation",
    "invoke_observed_agent_operation",
    # a365_otel_wrapper
    "invoke_observed_agent_operation_with_context",
    # agent_otel_extensions
    "configure_opentelemetry",
    "setup_health_routes",
    "create_aiohttp_tracing_middleware",
]

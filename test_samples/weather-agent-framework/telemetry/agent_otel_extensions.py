# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""OpenTelemetry configuration helpers for the Python Weather Agent.

Python port of AgentOTELExtensions.cs from sample-agent/telemetry.

Adds common observability services:
  - TracerProvider with resource metadata
  - MeterProvider with custom agent meters
  - aiohttp tracing middleware (excludes health-check paths)
  - /health and /alive endpoint registration

Exporter support (install the matching package to activate):
  - OTLP (Aspire, Jaeger, etc.):
      pip install opentelemetry-exporter-otlp-proto-grpc
  - Azure Monitor / Application Insights:
      pip install azure-monitor-opentelemetry-exporter
  - Console (default when no other exporter is configured)

To learn more about the local Aspire dashboard, see:
  https://learn.microsoft.com/dotnet/aspire/fundamentals/dashboard/standalone
"""

import logging
import os
import socket
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)

HEALTH_ENDPOINT_PATH = "/health"
ALIVENESS_ENDPOINT_PATH = "/alive"

_SERVICE_NAMESPACE = "Microsoft.Agents"
_SOURCE_NAME = "A365.AgentFramework"


# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------


def configure_opentelemetry(
    app_name: str = "A365.AgentFramework",
    environment: str = "development",
    otlp_endpoint: Optional[str] = None,
    azure_monitor_connection_string: Optional[str] = None,
) -> None:
    """Configure global TracerProvider, MeterProvider, and logging bridge.

    Equivalent to ``ConfigureOpenTelemetry()`` in C#.

    Call this **once at startup**, before any code creates spans or records
    metrics.  The OTel proxy objects in *agent_metrics.py* will automatically
    route to the real providers once this function has run.

    Args:
        app_name: Service name shown in traces/dashboards.
        environment: Deployment environment tag (e.g. ``"development"``,
            ``"production"``).
        otlp_endpoint: OTLP collector URL.  Falls back to the
            ``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable when *None*.
        azure_monitor_connection_string: Application Insights connection
            string.  Falls back to ``APPLICATIONINSIGHTS_CONNECTION_STRING``
            when *None*.
    """
    resource = Resource.create(
        {
            SERVICE_NAME: _SOURCE_NAME,
            SERVICE_VERSION: "1.0.0",
            SERVICE_INSTANCE_ID: socket.gethostname(),
            "deployment.environment": environment,
            "service.namespace": _SERVICE_NAMESPACE,
        }
    )

    _configure_tracing(resource, app_name, otlp_endpoint, azure_monitor_connection_string)
    _configure_metrics(resource, otlp_endpoint, azure_monitor_connection_string)
    _configure_logging()

    logger.info(
        "OpenTelemetry configured — service: %s, environment: %s",
        app_name,
        environment,
    )


def setup_health_routes(app, development: bool = True) -> None:
    """Register ``/health`` and ``/alive`` endpoints on an aiohttp Application.

    Equivalent to ``MapDefaultEndpoints()`` in C#.  Mirrors the C# behaviour
    of only registering the endpoints in non-production environments.

    Args:
        app: :class:`aiohttp.web.Application` instance.
        development: When ``False`` the endpoints are **not** registered
            (matches the C# guard on ``IsDevelopment()``).
    """
    if not development:
        return

    from aiohttp import web

    async def health_handler(_request):
        return web.Response(
            text='{"status":"Healthy"}',
            content_type="application/json",
        )

    async def alive_handler(_request):
        return web.Response(
            text='{"status":"Alive"}',
            content_type="application/json",
        )

    app.router.add_get(HEALTH_ENDPOINT_PATH, health_handler)
    app.router.add_get(ALIVENESS_ENDPOINT_PATH, alive_handler)
    logger.info(
        "Health check endpoints registered: %s, %s",
        HEALTH_ENDPOINT_PATH,
        ALIVENESS_ENDPOINT_PATH,
    )


def create_aiohttp_tracing_middleware():
    """Return an aiohttp middleware that traces every non-health-check request.

    Equivalent to the ``AddAspNetCoreInstrumentation()`` configuration in C#:
    - Filters out ``/health`` and ``/alive`` paths.
    - Enriches spans with ``http.request.body.size`` and ``user_agent`` on
      request, and ``http.status_code`` / ``http.response.body.size`` on
      response.
    - Records exceptions and sets the span status accordingly.
    """
    from aiohttp import web

    _tracer = trace.get_tracer(_SOURCE_NAME, "1.0.0")

    @web.middleware
    async def tracing_middleware(request, handler):
        # Exclude health check requests from tracing (mirrors C# filter lambda)
        if request.path.startswith(HEALTH_ENDPOINT_PATH) or request.path.startswith(
            ALIVENESS_ENDPOINT_PATH
        ):
            return await handler(request)

        span_name = f"{request.method} {request.path}"
        with _tracer.start_as_current_span(span_name) as span:
            # Enrich with request details — equivalent to EnrichWithHttpRequest
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.request.body.size", request.content_length or 0)
            user_agent = request.headers.get("User-Agent", "")
            if user_agent:
                span.set_attribute("user_agent", user_agent)

            try:
                response = await handler(request)
                # Enrich with response details — equivalent to EnrichWithHttpResponse
                span.set_attribute("http.status_code", response.status)
                span.set_attribute(
                    "http.response.body.size", response.content_length or 0
                )
                span.set_status(StatusCode.OK)
                return response
            except Exception as ex:
                span.set_status(StatusCode.ERROR, str(ex))
                span.record_exception(ex)
                raise

    return tracing_middleware


# ---------------------------------------------------------------------------
# Internal helpers — mirrors private methods in AgentOTELExtensions.cs
# ---------------------------------------------------------------------------


def _configure_tracing(
    resource: Resource,
    app_name: str,
    otlp_endpoint: Optional[str],
    azure_monitor_connection_string: Optional[str],
) -> None:
    """Build and register the global TracerProvider."""
    tracer_provider = TracerProvider(resource=resource)

    has_real_exporter = False

    # OTLP exporter — equivalent to UseOtlpExporter() in C#
    resolved_otlp = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if resolved_otlp:
        _add_otlp_trace_exporter(tracer_provider, resolved_otlp)
        has_real_exporter = True

    # Azure Monitor exporter — equivalent to UseAzureMonitor() in C#
    resolved_az = azure_monitor_connection_string or os.environ.get(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    if resolved_az:
        _add_azure_monitor_trace_exporter(tracer_provider, resolved_az)
        has_real_exporter = True

    # Console exporter for local development (no production exporter configured)
    if not has_real_exporter:
        _add_console_trace_exporter(tracer_provider)

    trace.set_tracer_provider(tracer_provider)


def _configure_metrics(
    resource: Resource,
    otlp_endpoint: Optional[str],
    azure_monitor_connection_string: Optional[str],
) -> None:
    """Build and register the global MeterProvider."""
    from opentelemetry import metrics

    readers = []

    resolved_otlp = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if resolved_otlp:
        reader = _create_otlp_metric_reader(resolved_otlp)
        if reader:
            readers.append(reader)

    resolved_az = azure_monitor_connection_string or os.environ.get(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    if resolved_az:
        reader = _create_azure_monitor_metric_reader(resolved_az)
        if reader:
            readers.append(reader)

    if not readers:
        readers.append(_create_console_metric_reader())

    meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meter_provider)


def _configure_logging() -> None:
    """Bridge Python logging to the OTEL LoggerProvider when available.

    Equivalent to ``builder.Logging.AddOpenTelemetry(...)`` in C#.
    Requires ``pip install opentelemetry-instrumentation-logging``.
    """
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        LoggingInstrumentor().instrument(set_logging_format=True)
        logger.debug("OTEL logging instrumentation enabled")
    except ImportError:
        logger.debug(
            "opentelemetry-instrumentation-logging not installed — "
            "Python log records will not be correlated with traces. "
            "Install with: pip install opentelemetry-instrumentation-logging"
        )


# -- Trace exporter helpers --------------------------------------------------


def _add_otlp_trace_exporter(
    tracer_provider: TracerProvider, endpoint: str
) -> None:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OTLP trace exporter → %s", endpoint)
    except ImportError:
        logger.warning(
            "OTLP trace exporter requested but package not found. "
            "Install: pip install opentelemetry-exporter-otlp-proto-grpc"
        )


def _add_azure_monitor_trace_exporter(
    tracer_provider: TracerProvider, connection_string: str
) -> None:
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

        exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("Azure Monitor trace exporter configured")
    except ImportError:
        logger.warning(
            "Azure Monitor trace exporter requested but package not found. "
            "Install: pip install azure-monitor-opentelemetry-exporter"
        )


def _add_console_trace_exporter(tracer_provider: TracerProvider) -> None:
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    logger.debug("Console span exporter active (development mode)")


# -- Metric reader helpers ----------------------------------------------------


def _create_otlp_metric_reader(endpoint: str) -> Optional[PeriodicExportingMetricReader]:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )

        exporter = OTLPMetricExporter(endpoint=endpoint)
        logger.info("OTLP metric exporter → %s", endpoint)
        return PeriodicExportingMetricReader(exporter)
    except ImportError:
        logger.warning(
            "OTLP metric exporter requested but package not found. "
            "Install: pip install opentelemetry-exporter-otlp-proto-grpc"
        )
        return None


def _create_azure_monitor_metric_reader(
    connection_string: str,
) -> Optional[PeriodicExportingMetricReader]:
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricsExporter

        exporter = AzureMonitorMetricsExporter(connection_string=connection_string)
        logger.info("Azure Monitor metric exporter configured")
        return PeriodicExportingMetricReader(exporter)
    except ImportError:
        logger.warning(
            "Azure Monitor metric exporter requested but package not found. "
            "Install: pip install azure-monitor-opentelemetry-exporter"
        )
        return None


def _create_console_metric_reader() -> PeriodicExportingMetricReader:
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter

    logger.debug("Console metric exporter active (development mode)")
    return PeriodicExportingMetricReader(ConsoleMetricExporter())

import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from . import constants

def configure_telemetry() -> None:
    """Configure OpenTelemetry with default exporters."""

    # Configure Tracing
    trace_provider = TracerProvider(resource=constants.RESOURCE)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter())
    )
    trace.set_tracer_provider(trace_provider)

    # Configure Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter()
    )
    meter_provider = MeterProvider(resource=constants.RESOURCE, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Configure Logging
    logger_provider = LoggerProvider(resource=constants.RESOURCE)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter())
    )
    set_logger_provider(logger_provider)

    # Add logging handler
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
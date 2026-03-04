import time
from typing import Callable, ContextManager
from datetime import datetime, timezone
from collections.abc import Iterator

from contextlib import contextmanager

from opentelemetry.metrics import Meter, Counter, Histogram, UpDownCounter
from opentelemetry import metrics, trace
from opentelemetry.trace import Tracer, Span

from microsoft_agents.hosting.core.turn_context import TurnContext

from . import constants

def _ts() -> float:
    """Helper function to get current timestamp in milliseconds"""
    return datetime.now(timezone.utc).timestamp() * 1000

class _AgentsTelemetry:

    _tracer: Tracer
    _meter: Meter

    # not thread-safe
    _message_processed_counter: Counter
    _route_executed_counter: Counter
    _message_processing_duration: Histogram
    _route_execution_duration: Histogram
    _message_processing_duration: Histogram
    _active_conversations: UpDownCounter

    def __init__(self, tracer: Tracer | None = None, meter: Meter | None = None):
        if tracer is None:
             tracer = trace.get_tracer(constants.SERVICE_NAME, constants.SERVICE_VERSION)
        if meter is None:
            meter = metrics.get_meter(constants.SERVICE_NAME, constants.SERVICE_VERSION)

        self._meter = meter
        self._tracer = tracer

        # Storage

        self._storage_operations = self._meter.create_counter(
            constants.STORAGE_OPERATION_TOTAL_METRIC_NAME,
            "operation",
            description="Number of storage operations performed by the agent",
        )

        self._storage_operation_duration = self._meter.create_histogram(
            constants.STORAGE_OPERATION_DURATION_METRIC_NAME,
            "ms",
            description="Duration of storage operations in milliseconds",
        )

        # AgentApplication

        self._turn_total = self._meter.create_counter(
            constants.AGENT_TURN_TOTAL_METRIC_NAME,
            "turn",
            description="Total number of turns processed by the agent",
        )

        self._turn_errors = self._meter.create_counter(
            constants.AGENT_TURN_ERRORS_METRIC_NAME,
            "turn",
            description="Number of turns that resulted in an error",
        )

        self._turn_duration = self._meter.create_histogram(
            constants.AGENT_TURN_DURATION_METRIC_NAME,
            "ms",
            description="Duration of agent turns in milliseconds",
        )

        # Adapters

        self._adapter_process_duration = self._meter.create_histogram(
            constants.ADAPTER_PROCESS_DURATION_METRIC_NAME,
            "ms",
            description="Duration of adapter processing in milliseconds",
        )

        # Connectors

        self._connector_request_total = self._meter.create_counter(
            constants.CONNECTOR_REQUEST_TOTAL_METRIC_NAME,
            "request",
            description="Total number of connector requests made by the agent",
        )

        self._connector_request_duration = self._meter.create_histogram(
            constants.CONNECTOR_REQUEST_DURATION_METRIC_NAME,
            "ms",
            description="Duration of connector requests in milliseconds",
        )

        # Auth

        self._auth_token_request_total = self._meter.create_counter(
            constants.AUTH_TOKEN_REQUEST_TOTAL_METRIC_NAME,
            "request",
            description="Total number of auth token requests made by the agent",
        )

        self._auth_token_requests_duration = self._meter.create_histogram(
            constants.AUTH_TOKEN_REQUEST_DURATION_METRIC_NAME,
            "ms",
            description="Duration of auth token retrieval in milliseconds",
        )

    @property
    def tracer(self) -> Tracer:
        return self._tracer
    
    @property
    def meter(self) -> Meter:
        return self._meter

    def _extract_attributes_from_context(self, context: TurnContext) -> dict:
        # This can be expanded to extract common attributes for spans and metrics from the context
        attributes = {}
        attributes["activity.type"] = context.activity.type
        attributes["agent.is_agentic"] = context.activity.is_agentic_request()
        if context.activity.from_property:
            attributes["from.id"] = context.activity.from_property.id
        if context.activity.recipient:
            attributes["recipient.id"] = context.activity.recipient.id
        if context.activity.conversation:
            attributes["conversation.id"] = context.activity.conversation.id
        attributes["channel_id"] = context.activity.channel_id
        attributes["message.text.length"] = len(context.activity.text) if context.activity.text else 0
        return attributes

    @contextmanager
    def start_as_current_span(self, span_name: str, context: TurnContext) -> Iterator[Span]:
    
        with self._tracer.start_as_current_span(span_name) as span:
            attributes = self._extract_attributes_from_context(context)
            span.set_attributes(attributes)
            # span.add_event(f"{span_name} started", attributes)
            yield span

    @contextmanager
    def _start_timed_span(
        self,
        span_name: str,
        context: TurnContext | None = None,
        *,
        success_callback: Callable[[Span, float], None] | None = None,
        failure_callback: Callable[[Span, Exception], None] | None = None,
    ) -> Iterator[Span]:
        
        cm: ContextManager[Span]
        if context is None:
            cm = self._tracer.start_as_current_span(span_name)
        else:
            cm = self.start_as_current_span(span_name, context)

        with cm as span:

            start = time.time()
            exception: Exception | None = None

            try:
                yield span  # execute the operation in the with block
            except Exception as e:
                span.record_exception(e)
                exception = e
            finally:

                success = exception is None

                end = time.time()
                duration = (end - start) * 1000  # milliseconds

                span.add_event(f"{span_name} completed", {"duration_ms": duration})

                if success:
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    if success_callback:
                        success_callback(span, duration)
                else:

                    if failure_callback:
                        failure_callback(span, exception)

                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise exception from None # re-raise to ensure it's not swallowed
    
    @contextmanager
    def instrument_agent_turn(self, context: TurnContext) -> Iterator[Span]:
        """Context manager for recording an agent turn, including success/failure and duration"""

        def success_callback(span: Span, duration: float):
            self._turn_total.add(1)
            self._turn_duration.record(duration, {
                "conversation.id": context.activity.conversation.id if context.activity.conversation else "unknown",
                "channel.id": str(context.activity.channel_id),
            })

            # ts = int(datetime.now(timezone.utc).timestamp())
            # span.add_event(
            #     "message.processed",
            #     {
            #         "agent.is_agentic": context.activity.is_agentic_request(),
            #         "activity.type": context.activity.type,
            #        ddd "channel.id": str(context.activity.channel_id),
            #         "message.id": str(context.activity.id),
            #         "message.text": context.activity.text,
            #     },
            #     ts,
            # )

        def failure_callback(span: Span, e: Exception):
            self._turn_errors.add(1)

        with self._start_timed_span(
            constants.AGENT_TURN_OPERATION_NAME,
            context=context,
            success_callback=success_callback,
            failure_callback=failure_callback
        ) as span:
            yield span  # execute the turn operation in the with block            

    @contextmanager
    def instrument_adapter_process(self):
        """Context manager for recording adapter processing operations"""

        def success_callback(span: Span, duration: float):
            self._adapter_process_duration.record(duration)

        with self._start_timed_span(
            constants.ADAPTER_PROCESS_OPERATION_NAME,
            success_callback=success_callback
        ) as span:
            yield span  # execute the adapter processing in the with block

    @contextmanager
    def instrument_storage_op(self, operation_name: str):
        """Context manager for recording storage operations"""

        def success_callback(span: Span, duration: float):
            self._storage_operations.add(1, {"operation": operation_name})
            self._storage_operation_duration.record(duration, {"operation": operation_name})

        with self._start_timed_span(
            constants.STORAGE_OPERATION_NAME_FORMAT.format(operation_name=operation_name),
            success_callback=success_callback
        ) as span:
            yield span  # execute the storage operation in the with block

    @contextmanager
    def instrument_connector_op(self, operation_name: str):
        """Context manager for recording connector requests"""

        def success_callback(span: Span, duration: float):
            self._connector_request_total.add(1, {"operation": operation_name})
            self._connector_request_duration.record(duration, {"operation": operation_name})

        with self._start_timed_span(
            constants.CONNECTOR_REQUEST_OPERATION_NAME_FORMAT.format(operation_name=operation_name),
            success_callback=success_callback
        ) as span:
            yield span  # execute the connector request in the with block

    @contextmanager
    def instrument_auth_token_request(self):
        """Context manager for recording auth token retrieval operations"""

        def success_callback(span: Span, duration: float):
            self._auth_token_request_total.add(1)
            self._auth_token_requests_duration.record(duration)

        with self._start_timed_span(
            constants.AUTH_TOKEN_REQUEST_OPERATION_NAME,
            success_callback=success_callback
        ) as span:
            yield span  # execute the auth token retrieval operation in the with block

agents_telemetry = _AgentsTelemetry()
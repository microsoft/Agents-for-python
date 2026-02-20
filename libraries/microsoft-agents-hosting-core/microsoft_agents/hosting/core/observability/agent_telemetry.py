import time
from typing import Callable, ContextManager
from datetime import datetime, timezone
from collections.abc import Iterator

from contextlib import contextmanager

from microsoft_agents.hosting.core import TurnContext

from opentelemetry.metrics import Meter, Counter, Histogram, UpDownCounter
from opentelemetry import metrics, trace
from opentelemetry.trace import Tracer, Span

from .types import StorageOperation

def _ts() -> float:
    """Helper function to get current timestamp in milliseconds"""
    return datetime.now(timezone.utc).timestamp() * 1000

class AgentTelemetry:

    tracer: Tracer
    meter: Meter

    # not thread-safe
    _message_processed_counter: Counter
    _route_executed_counter: Counter
    _message_processing_duration: Histogram
    _route_execution_duration: Histogram
    _message_processing_duration: Histogram
    _active_conversations: UpDownCounter

    def __init__(self):
        self.tracer = trace.get_tracer("M365.agents", "1.0.0")
        self.meter = metrics.get_meter("M365.agents", "1.0.0")

        self._turns_total = self.meter.create_counter(
            "agents.turns.total",
            "turn",
            description="Total number of turns processed by the agent",
        )

        self._turns_errors = self.meter.create_counter(
            "agents.turns.errors",
            "turn",
            description="Number of turns that resulted in an error",
        )

        self._storage_operations = self.meter.create_counter(
            "agents.storage.operations",
            "operation",
            description="Number of storage operations performed by the agent",
        )

        self._turn_duration = self.meter.create_histogram(
            "agents.turn.duration",
            "ms",
            description="Duration of agent turns in milliseconds",
        )

        self._adapter_process_duration = self.meter.create_histogram(
            "agents.adapter.process.duration",
            "ms",
            description="Duration of adapter processing in milliseconds",
        )

        self._storage_operation_duration = self.meter.create_histogram(
            "agents.storage.operation.duration",
            "ms",
            description="Duration of storage operations in milliseconds",
        )

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
    
        with self.tracer.start_as_current_span(span_name) as span:
            attributes = self._extract_attributes_from_context(context)
            span.set_attributes(attributes)
            # span.add_event(f"{span_name} started", attributes)
            yield span

    @contextmanager
    def _timed_span(
        self,
        span_name: str,
        context: TurnContext | None = None,
        *,
        success_callback: Callable[[Span, float], None] | None = None,
        failure_callback: Callable[[Span, Exception], None] | None = None,
    ) -> Iterator[Span]:
        
        cm: ContextManager[Span]
        if context is None:
            cm = self.tracer.start_as_current_span(span_name)
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
                    raise exception  # re-raise to ensure it's not swallowed
    
    @contextmanager
    def agent_turn_operation(self, context: TurnContext) -> Iterator[Span]:
        """Context manager for recording an agent turn, including success/failure and duration"""

        def success_callback(span: Span, duration: float):
            self._turns_total.add(1)
            self._turn_duration.record(duration, {
                "conversation.id": context.activity.conversation.id if context.activity.conversation else "unknown",
                "channel.id": str(context.activity.channel_id),
            })

            ts = int(datetime.now(timezone.utc).timestamp())
            span.add_event(
                "message.processed",
                {
                    "agent.is_agentic": context.activity.is_agentic_request(),
                    "activity.type": context.activity.type,
                    "channel.id": str(context.activity.channel_id),
                    "message.id": str(context.activity.id),
                    "message.text": context.activity.text,
                },
                ts,
            )

        def failure_callback(span: Span, e: Exception):
            self._turns_errors.add(1)

        with self._timed_span(
            "agent turn",
            context=context,
            success_callback=success_callback,
            failure_callback=failure_callback
        ) as span:
            yield span  # execute the turn operation in the with block            

    @contextmanager
    def adapter_process_operation(self, operation_name: str, context: TurnContext):
        """Context manager for recording adapter processing operations"""

        def success_callback(span: Span, duration: float):
            self._adapter_process_duration.record(duration, {
                "conversation.id": context.activity.conversation.id if context.activity.conversation else "unknown",
                "channel.id": str(context.activity.channel_id),
            })


        with self._timed_span(
            "adapter process",
            context,
            success_callback=success_callback
        ) as span:
            yield span  # execute the adapter processing in the with block

    @contextmanager
    def storage_operation(self, operation: StorageOperation):
        """Context manager for recording storage operations"""

        def success_callback(span: Span, duration: float):
            self._storage_operations.add(1, {"operation": operation.value})
            self._storage_operation_duration.record(duration, {"operation": operation.value})

        with self._timed_span(
            f"storage {operation.value}",
            success_callback=success_callback
        ) as span:
            yield span  # execute the storage operation in the with block

agent_telemetry = AgentTelemetry()

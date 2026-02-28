import time
from datetime import datetime, timezone

from contextlib import contextmanager

from microsoft_agents.hosting.core import TurnContext

from opentelemetry.metrics import Meter, Counter, Histogram, UpDownCounter
from opentelemetry import metrics, trace
from opentelemetry.trace import Tracer, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


class AgentMetrics:

    tracer: Tracer

    # not thread-safe
    _message_processed_counter: Counter
    _route_executed_counter: Counter
    _message_processing_duration: Histogram
    _route_execution_duration: Histogram
    _message_processing_duration: Histogram
    _active_conversations: UpDownCounter

    def __init__(self):
        self.tracer = trace.get_tracer("A365.AgentFramework")
        self.meter = metrics.get_meter("A365.AgentFramework", "1.0.0")

        self._message_processed_counter = self.meter.create_counter(
            "agents.message.processed.count",
            "messages",
            description="Number of messages processed by the agent",
        )
        self._route_executed_counter = self.meter.create_counter(
            "agents.route.executed.count",
            "routes",
            description="Number of routes executed by the agent",
        )
        self._message_processing_duration = self.meter.create_histogram(
            "agents.message.processing.duration",
            "ms",
            description="Duration of message processing in milliseconds",
        )
        self._route_execution_duration = self.meter.create_histogram(
            "agents.route.execution.duration",
            "ms",
            description="Duration of route execution in milliseconds",
        )
        self._active_conversations = self.meter.create_up_down_counter(
            "agents.active.conversations.count",
            "conversations",
            description="Number of active conversations",
        )

    def _finalize_message_handling_span(
        self, span: Span, context: TurnContext, duration_ms: float, success: bool
    ):
        self._message_processing_duration.record(
            duration_ms,
            {
                "conversation.id": (
                    context.activity.conversation.id
                    if context.activity.conversation
                    else "unknown"
                ),
                "channel.id": str(context.activity.channel_id),
            },
        )
        self._route_executed_counter.add(
            1,
            {
                "route.type": "message_handler",
                "conversation.id": (
                    context.activity.conversation.id
                    if context.activity.conversation
                    else "unknown"
                ),
            },
        )

        if success:
            span.set_status(trace.Status(trace.StatusCode.OK))
        else:
            span.set_status(trace.Status(trace.StatusCode.ERROR))

    @contextmanager
    def http_operation(self, operation_name: str):

        with self.tracer.start_as_current_span(operation_name) as span:

            span.set_attribute("operation.name", operation_name)
            span.add_event("Agent operation started", {})

            try:
                yield  # execute the operation in the with block
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                raise

    @contextmanager
    def _init_span_from_context(self, operation_name: str, context: TurnContext):

        with self.tracer.start_as_current_span(operation_name) as span:

            span.set_attribute("activity.type", context.activity.type)
            span.set_attribute(
                "agent.is_agentic", context.activity.is_agentic_request()
            )
            if context.activity.from_property:
                span.set_attribute("caller.id", context.activity.from_property.id)
            if context.activity.conversation:
                span.set_attribute("conversation.id", context.activity.conversation.id)
            span.set_attribute("channel_id", str(context.activity.channel_id))
            span.set_attribute(
                "message.text.length",
                len(context.activity.text) if context.activity.text else 0,
            )

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

            yield span

    @contextmanager
    def agent_operation(self, operation_name: str, context: TurnContext):

        self._message_processed_counter.add(1)

        with self._init_span_from_context(operation_name, context) as span:

            start = time.time()

            span.set_attribute("operation.name", operation_name)
            span.add_event("Agent operation started", {})

            success = True

            try:
                yield  # execute the operation in the with block
            except Exception as e:
                success = False
                span.record_exception(e)
                raise
            finally:

                end = time.time()
                duration = (end - start) * 1000  # milliseconds

                self._finalize_message_handling_span(span, context, duration, success)


agent_metrics = AgentMetrics()

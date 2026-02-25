# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Agent metrics and distributed tracing for OpenTelemetry instrumentation.

Python port of AgentMetrics.cs from sample-agent/telemetry.

Provides:
- An ActivitySource-equivalent tracer named "A365.AgentFramework"
- A Meter with the same name for counters, histograms, and up-down counters
- Helper functions to start/finalize message-handling spans
- Observed-operation wrappers (sync and async)
"""

import logging
import time
from typing import Awaitable, Callable

from opentelemetry import context as otel_context
from opentelemetry import metrics, trace
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)

# Equivalent to ActivitySource name in C#
SOURCE_NAME = "A365.AgentFramework"

# Tracer — equivalent to `new ActivitySource(SourceName)` in C#
# Uses a ProxyTracer until configure_opentelemetry() sets a real TracerProvider.
tracer = trace.get_tracer(SOURCE_NAME, "1.0.0")

# Meter — equivalent to `new Meter("A365.AgentFramework", "1.0.0")` in C#
meter = metrics.get_meter(SOURCE_NAME, "1.0.0")

# ---------------------------------------------------------------------------
# Metrics — mirrors the static Counter/Histogram/UpDownCounter fields in C#
# ---------------------------------------------------------------------------

message_processed_counter = meter.create_counter(
    "agent.messages.processed",
    unit="messages",
    description="Number of messages processed by the agent",
)

route_executed_counter = meter.create_counter(
    "agent.routes.executed",
    unit="routes",
    description="Number of routes executed by the agent",
)

message_processing_duration = meter.create_histogram(
    "agent.message.processing.duration",
    unit="ms",
    description="Duration of message processing in milliseconds",
)

route_execution_duration = meter.create_histogram(
    "agent.route.execution.duration",
    unit="ms",
    description="Duration of route execution in milliseconds",
)

active_conversations = meter.create_up_down_counter(
    "agent.conversations.active",
    unit="conversations",
    description="Number of active conversations",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_activity_attrs(context) -> dict:
    """Extract activity attributes from a TurnContext."""
    attrs: dict = {}
    activity = getattr(context, "activity", None)
    if activity is None:
        return attrs

    attrs["Activity.Type"] = str(getattr(activity, "type", "") or "")

    # 'from' is a Python keyword; the SDK stores it as from_property or _from.
    from_obj = (
        getattr(activity, "from_property", None)
        or getattr(activity, "_from", None)
        # getattr with string "from" works at runtime despite being a keyword
        or getattr(activity, "from", None)
    )
    attrs["Caller.Id"] = str(getattr(from_obj, "id", "") or "")

    conversation = getattr(activity, "conversation", None)
    attrs["Conversation.Id"] = str(getattr(conversation, "id", "") or "")
    attrs["Channel.Id"] = str(getattr(activity, "channel_id", "") or "")

    text = getattr(activity, "text", "") or ""
    attrs["Message.Text.Length"] = len(text)
    attrs["Message.Id"] = str(getattr(activity, "id", "") or "")
    attrs["Message.Text"] = text[:200]  # truncate to avoid oversized attributes

    return attrs


# ---------------------------------------------------------------------------
# Public API — mirrors AgentMetrics static methods in C#
# ---------------------------------------------------------------------------

def initialize_message_handling_span(handler_name: str, context) -> trace.Span:
    """Start a tracing span with contextual tags from the turn activity.

    Equivalent to ``InitializeMessageHandlingActivity()`` in C#.

    The caller is responsible for ending the span (use
    ``finalize_message_handling_span`` or call ``span.end()`` directly).

    Args:
        handler_name: Name used as the span name (e.g. ``"OnMessageActivity"``).
        context: TurnContext whose activity fields are attached as span attributes.

    Returns:
        A started (but not yet current) :class:`opentelemetry.trace.Span`.
    """
    span = tracer.start_span(handler_name)
    attrs = _get_activity_attrs(context)

    # Set individual attributes on the span (mirrors activity?.SetTag calls in C#)
    for key in ("Activity.Type", "Caller.Id", "Conversation.Id", "Channel.Id"):
        span.set_attribute(key, attrs.get(key, ""))
    span.set_attribute("Message.Text.Length", attrs.get("Message.Text.Length", 0))
    # Tag whether the request came from an agentic caller
    span.set_attribute("Agent.IsAgentic", bool(getattr(getattr(context, "activity", None), "is_agentic", False)))

    # Equivalent to activity?.AddEvent(new ActivityEvent("Message.Processed", ...))
    span.add_event(
        "Message.Processed",
        attributes={
            "Caller.Id": attrs.get("Caller.Id", ""),
            "Channel.Id": attrs.get("Channel.Id", ""),
            "Message.Id": attrs.get("Message.Id", ""),
            "Message.Text": attrs.get("Message.Text", ""),
        },
    )
    return span


def finalize_message_handling_span(
    span: trace.Span,
    context,
    duration_ms: float,
    success: bool,
) -> None:
    """Record duration metrics and end the span.

    Equivalent to ``FinalizeMessageHandlingActivity()`` in C#.

    Args:
        span: The span returned by :func:`initialize_message_handling_span`.
        context: TurnContext used to label the metric dimensions.
        duration_ms: Elapsed time in milliseconds.
        success: ``True`` → span status OK; ``False`` → span status ERROR.
    """
    attrs = _get_activity_attrs(context)
    conversation_id = attrs.get("Conversation.Id") or "unknown"
    channel_id = attrs.get("Channel.Id") or "unknown"

    message_processing_duration.record(
        duration_ms,
        {"Conversation.Id": conversation_id, "Channel.Id": channel_id},
    )

    route_executed_counter.add(
        1,
        {"Route.Type": "message_handler", "Conversation.Id": conversation_id},
    )

    span.set_status(StatusCode.OK if success else StatusCode.ERROR)
    span.end()


def invoke_observed_http_operation(operation_name: str, func: Callable) -> None:
    """Wrap a synchronous callable with a tracing span.

    Equivalent to ``InvokeObservedHttpOperation()`` in C#.

    Args:
        operation_name: Span name.
        func: Synchronous callable to execute.
    """
    with tracer.start_as_current_span(operation_name) as span:
        try:
            func()
            span.set_status(StatusCode.OK)
        except Exception as ex:
            span.set_status(StatusCode.ERROR, str(ex))
            span.record_exception(ex)
            raise


async def invoke_observed_agent_operation(
    operation_name: str,
    context,
    func: Callable[[], Awaitable[None]],
) -> None:
    """Async wrapper for an agent operation with full metrics and tracing.

    Equivalent to ``AgentMetrics.InvokeObservedAgentOperation()`` in C#.

    Increments the message-processed counter, opens a span, sets it as the
    current context, awaits *func*, then records the duration and finalises
    the span.

    Args:
        operation_name: Span / operation name.
        context: TurnContext used for span attributes and metric labels.
        func: Async function containing the agent logic.
    """
    message_processed_counter.add(1)

    span = initialize_message_handling_span(operation_name, context)
    # Make the span the active span for the duration of the call
    ctx = trace.set_span_in_context(span)
    token = otel_context.attach(ctx)

    start_time = time.monotonic()
    success = True
    try:
        await func()
    except Exception as ex:
        success = False
        span.set_status(StatusCode.ERROR, str(ex))
        span.record_exception(ex)
        raise
    finally:
        otel_context.detach(token)
        duration_ms = (time.monotonic() - start_time) * 1000
        finalize_message_handling_span(span, context, duration_ms, success)

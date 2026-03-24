# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import time
import logging
from collections.abc import Iterator

from contextlib import contextmanager

from opentelemetry.metrics import Meter
from opentelemetry import metrics, trace
from opentelemetry.trace import Tracer, Span

from microsoft_agents.activity import TurnContextProtocol

from .resource import SERVICE_NAME, SERVICE_VERSION
from .type_defs import SpanCallback

logger = logging.getLogger(__name__)


class _AgentsTelemetry:

    def __init__(self):
        """Initializes the AgentsTelemetry instance with the given tracer and meter, or creates new ones if not provided

        :param tracer: Optional OpenTelemetry Tracer instance to use for creating spans. If not provided, a new tracer will be created with the service name and version from constants.
        :param meter: Optional OpenTelemetry Meter instance to use for recording metrics. If not provided, a new meter will be created with the service name and version from constants.
        """
        self._tracer = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)
        self._meter = metrics.get_meter(SERVICE_NAME, SERVICE_VERSION)

    @property
    def tracer(self) -> Tracer:
        """Returns the OpenTelemetry tracer instance for creating spans"""
        return self._tracer

    @property
    def meter(self) -> Meter:
        """Returns the OpenTelemetry meter instance for recording metrics"""
        return self._meter

    def _extract_attributes_from_context(
        self, turn_context: TurnContextProtocol
    ) -> dict:
        """Helper method to extract common attributes from the TurnContext for span and metric recording"""

        # This can be expanded to extract common attributes for spans and metrics from the context
        attributes = {}
        attributes["activity.type"] = turn_context.activity.type
        attributes["agent.is_agentic"] = turn_context.activity.is_agentic_request()
        if turn_context.activity.from_property:
            attributes["from.id"] = turn_context.activity.from_property.id
        if turn_context.activity.recipient:
            attributes["recipient.id"] = turn_context.activity.recipient.id
        if turn_context.activity.conversation:
            attributes["conversation.id"] = turn_context.activity.conversation.id
        attributes["channel_id"] = turn_context.activity.channel_id
        attributes["message.text.length"] = (
            len(turn_context.activity.text) if turn_context.activity.text else 0
        )
        return attributes

    def set_attributes_from_context(
        self, span: Span, turn_context: TurnContextProtocol
    ) -> None:
        """Extracts attributes from the TurnContext and sets them on the given span

        :param span: The OpenTelemetry span to set attributes on
        :param turn_context: The TurnContext to extract attributes from
        """
        span.set_attributes(self._extract_attributes_from_context(turn_context))

    @contextmanager
    def start_as_current_span(
        self,
        span_name: str,
        callback: SpanCallback | None = None,
    ) -> Iterator[Span]:
        """Context manager for starting a timed span that records duration and success/failure status, and invokes a callback with the results

        :param span_name: The name of the span to start
        :param callback: Optional callback function that will be called with the span, duration in milliseconds, and any exception that was raised (or None if successful) when the span is ended
        :return: An iterator that yields the started span, which will be ended when the context manager exits
        """

        with self._tracer.start_as_current_span(span_name) as span:

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

                if success:
                    span.add_event(f"{span_name} completed", {"duration_ms": duration})
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    if callback:
                        callback(span, duration, None)
                else:
                    if callback:
                        callback(span, duration, exception)

                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise exception from None  # re-raise to ensure it's not swallowed


agents_telemetry = _AgentsTelemetry()

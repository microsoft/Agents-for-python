# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC
from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry.trace import Span

from ._agents_telemetry import agents_telemetry
from .base_span_wrapper import BaseSpanWrapper
from .type_defs import AttributeMap


class SimpleSpanWrapper(BaseSpanWrapper, ABC):
    """Simple implementation of the BaseSpanWrapper that can be used when no additional attributes or functionality are needed on the span beyond what is provided by the base BaseSpanWrapper class. This can be used as a simple wrapper around an OTEL span for cases where no SDK-specific telemetry is needed, while still providing the benefits of the BaseSpanWrapper abstraction and lifecycle management."""

    def __init__(self, span_name: str):
        super().__init__()
        self._span_name = span_name

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This can be overridden by subclasses to provide custom attributes for the span based on the context in which it is being used."""
        return {}

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This can be overridden by subclasses to provide custom logic for recording metrics or handling errors based on the outcome of the span."""
        pass

    @contextmanager
    def _start_span(self) -> Iterator[Span]:
        """Starts a basic OTEL span with the given name and no additional attributes."""
        with agents_telemetry.start_as_current_span(
            self._span_name, callback=self._callback
        ) as span:
            try:
                yield span
            except Exception:
                raise
            finally:
                if span is not None:
                    attributes = self._get_attributes()
                    if attributes:
                        span.set_attributes(attributes)

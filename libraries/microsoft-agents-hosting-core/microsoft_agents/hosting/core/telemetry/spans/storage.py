# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span

from ..core import (
    constants,
    SimpleSpanWrapper,
)
from .. import _metrics

class _StorageSpanWrapper(SimpleSpanWrapper):
    """Base SpanWrapper for spans related to storage operations. This is meant to be a base class for spans related to storage operations, such as retrieving or saving state, and can be used to share common functionality and attributes related to storage operations."""

    def __init__(self, span_name: str, *, key_count: int):
        """Initializes the _StorageSpanWrapper span."""
        super().__init__(span_name)
        self._key_count = key_count

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the storage operation based on the outcome of the span."""
        _metrics.storage_operation_duration.record(duration)
        _metrics.storage_operation_total.add(1)

    def _get_attributes(self) -> dict[str, str]:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the storage operation being performed.

        NOTE: a dict is the annotated return type to allow child classes to add additional attributes.
        """
        return {
            constants.ATTR_KEY_COUNT: self._key_count,
        }
    
class StorageRead(_StorageSpanWrapper):
    """Span for reading from storage."""

    def __init__(self, key_count: int):
        """Initializes the StorageRead span."""
        super().__init__(constants.SPAN_STORAGE_READ, key_count=key_count)

class StorageWrite(_StorageSpanWrapper):
    """Span for writing to storage."""

    def __init__(self, key_count: int):
        """Initializes the StorageWrite span."""
        super().__init__(constants.SPAN_STORAGE_WRITE, key_count=key_count)

class StorageDelete(_StorageSpanWrapper):
    """Span for deleting from storage."""

    def __init__(self, key_count: int):
        """Initializes the StorageDelete span."""
        super().__init__(constants.SPAN_STORAGE_DELETE, key_count=key_count)
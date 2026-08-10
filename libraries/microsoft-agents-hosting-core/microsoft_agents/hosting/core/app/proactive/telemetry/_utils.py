# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from opentelemetry.trace import SpanContext

def _dump_span_context(span_context: SpanContext) -> dict:
    """Dumps a SpanContext into a dictionary.

    :param span_context: The SpanContext to serialize
    :type span_context: SpanContext
    :return: A dictionary representation of the SpanContext
    :rtype: dict
    """
    data = {
        "trace_id": span_context.trace_id,
        "span_id": span_context.span_id,
        "trace_flags": int(span_context.trace_flags),
        "trace_state": list(span_context.trace_state),
        "is_remote": span_context.is_remote,
    }
    return data

def _deserialize_span_context(data: dict) -> SpanContext:
    """Deserializes a dictionary into a SpanContext.

    :param data: The dictionary representation of the SpanContext
    :type data: dict
    :return: The deserialized SpanContext
    :rtype: SpanContext
    """
    return SpanContext(
        trace_id=data["trace_id"],
        span_id=data["span_id"],
        trace_flags=data["trace_flags"],
        trace_state=data["trace_state"],
        is_remote=data["is_remote"],
    )
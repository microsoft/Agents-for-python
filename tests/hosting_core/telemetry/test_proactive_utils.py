# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from opentelemetry.trace import SpanContext, TraceFlags, TraceState

from microsoft_agents.hosting.core.app.proactive.telemetry._utils import (
    _deserialize_span_context,
    _dump_span_context,
)


def _make_span_context(
    *,
    is_remote: bool = False,
    trace_flags: TraceFlags = TraceFlags(TraceFlags.SAMPLED),
    trace_state: TraceState | None = None,
) -> SpanContext:
    return SpanContext(
        trace_id=0x4BF92F3577B34DA6A3CE929D0E0E4736,
        span_id=0x00F067AA0BA902B7,
        is_remote=is_remote,
        trace_flags=trace_flags,
        trace_state=trace_state or TraceState(),
    )


def test_dump_span_context_serializes_all_fields():
    context = _make_span_context(
        is_remote=True,
        trace_state=TraceState([("vendor", "value")]),
    )

    result = _dump_span_context(context)

    assert result == {
        "trace_id": str(context.trace_id),
        "span_id": str(context.span_id),
        "trace_flags": int(context.trace_flags),
        "trace_state": [("vendor", "value")],
        "is_remote": True,
    }


def test_dump_span_context_serializes_empty_trace_state():
    context = _make_span_context()

    result = _dump_span_context(context)

    assert result["trace_state"] == []


def test_deserialize_span_context_restores_all_fields():
    result = _deserialize_span_context(
        {
            "trace_id": 0x4BF92F3577B34DA6A3CE929D0E0E4736,
            "span_id": 0x00F067AA0BA902B7,
            "trace_flags": TraceFlags.SAMPLED,
            "trace_state": [("vendor", "value")],
            "is_remote": True,
        }
    )

    assert result.trace_id == 0x4BF92F3577B34DA6A3CE929D0E0E4736
    assert result.span_id == 0x00F067AA0BA902B7
    assert result.trace_flags == TraceFlags(TraceFlags.SAMPLED)
    assert result.trace_state == TraceState([("vendor", "value")])
    assert result.is_remote is True
    assert result.is_valid is True


def test_deserialize_span_context_restores_unsampled_flags():
    result = _deserialize_span_context(
        {
            "trace_id": 1,
            "span_id": 2,
            "trace_flags": TraceFlags.DEFAULT,
            "trace_state": [],
            "is_remote": False,
        }
    )

    assert result.trace_flags == TraceFlags(TraceFlags.DEFAULT)
    assert result.trace_flags.sampled is False


def test_span_context_round_trip_preserves_context():
    context = _make_span_context(
        is_remote=True,
        trace_state=TraceState(
            [
                ("vendor", "value"),
                ("tenant", "contoso"),
            ]
        ),
    )

    result = _deserialize_span_context(_dump_span_context(context))

    assert result == context


def test_invalid_span_context_round_trip_remains_invalid():
    context = SpanContext(
        trace_id=0,
        span_id=0,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.DEFAULT),
        trace_state=TraceState(),
    )

    result = _deserialize_span_context(_dump_span_context(context))

    assert result.is_valid is False

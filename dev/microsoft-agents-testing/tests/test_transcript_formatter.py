# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the microsoft_agents.testing.formatting module."""

import json
import pytest
from datetime import datetime, timedelta, timezone

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core import Transcript, Exchange
from microsoft_agents.testing.formatting import (
    ActivityTranscriptFormatter,
    BaseTranscriptFormatter,
    ConversationTranscriptFormatter,
    JsonTranscriptFormatter,
    TranscriptFormatter,
    print_activities,
    print_conversation,
    print_json,
)
from microsoft_agents.testing.formatting.utils import (
    _exchange_sort_key,
    _format_timestamp,
)

T0 = datetime(2026, 2, 6, 10, 0, 0, 0)
T1 = T0 + timedelta(seconds=1, milliseconds=234)
T2 = T0 + timedelta(seconds=2, milliseconds=500)
T3 = T0 + timedelta(seconds=5)


# ============================================================================
# Fixtures / helpers
# ============================================================================


def _make_activity(
    type: str = ActivityTypes.message,
    text: str | None = None,
    role: str | None = None,
    timestamp: datetime | None = None,
    **kwargs,
) -> Activity:
    data: dict = {"type": type, **kwargs}
    if text is not None:
        data["text"] = text
    if role is not None:
        data["from_property"] = {"role": role}
    if timestamp is not None:
        data["timestamp"] = timestamp
    return Activity.model_validate(data)


def _user(text: str, timestamp: datetime | None = None) -> Activity:
    return _make_activity(text=text, role="user", timestamp=timestamp)


def _agent(text: str, timestamp: datetime | None = None) -> Activity:
    return _make_activity(text=text, role="bot", timestamp=timestamp)


def _make_exchange(
    request: Activity | None = None,
    responses: list[Activity] | None = None,
    request_at: datetime | None = None,
    response_at: datetime | None = None,
    error: str | None = None,
    status_code: int | None = 200,
) -> Exchange:
    return Exchange(
        request=request,
        request_at=request_at,
        responses=responses or [],
        response_at=response_at,
        error=error,
        status_code=status_code,
    )


def _transcript(*exchanges: Exchange) -> Transcript:
    t = Transcript()
    for ex in exchanges:
        t.record(ex)
    return t


# ============================================================================
# _exchange_sort_key
# ============================================================================


class TestExchangeSortKey:
    def test_sort_by_request_at(self):
        e1 = _make_exchange(request_at=T2)
        e2 = _make_exchange(request_at=T0)
        result = sorted([e1, e2], key=_exchange_sort_key)
        assert result[0].request_at == T0
        assert result[1].request_at == T2

    def test_falls_back_to_response_at(self):
        e = Exchange(response_at=T1, responses=[])
        assert _exchange_sort_key(e) == (T1,)

    def test_returns_datetime_min_when_both_none(self):
        e = Exchange(responses=[])
        assert _exchange_sort_key(e) == (datetime.min,)

    def test_prefers_request_at_over_response_at(self):
        e = _make_exchange(request_at=T0, response_at=T2)
        assert _exchange_sort_key(e) == (T0,)

    def test_strips_timezone_for_comparison(self):
        aware = T0.replace(tzinfo=timezone.utc)
        e = _make_exchange(request_at=aware)
        assert _exchange_sort_key(e) == (T0,)


# ============================================================================
# _format_timestamp
# ============================================================================


class TestFormatTimestamp:
    def test_formats_hours_minutes_seconds_millis(self):
        assert (
            _format_timestamp(datetime(2026, 2, 6, 14, 30, 45, 123456))
            == "14:30:45.123"
        )

    def test_returns_placeholder_for_none(self):
        assert _format_timestamp(None) == "??:??.???"

    def test_truncates_microseconds_to_milliseconds(self):
        assert (
            _format_timestamp(datetime(2026, 1, 1, 0, 0, 0, 999999)) == "00:00:00.999"
        )

    def test_midnight(self):
        assert _format_timestamp(datetime(2026, 1, 1, 0, 0, 0, 0)) == "00:00:00.000"


# ============================================================================
# BaseTranscriptFormatter
# ============================================================================


class TestBaseTranscriptFormatter:
    def test_call_delegates_to_format(self):
        class Echo(BaseTranscriptFormatter):
            def format(self, transcript: Transcript) -> str:
                return "ok"

        assert Echo()(_transcript()) == "ok"

    def test_format_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            BaseTranscriptFormatter().format(_transcript())


# ============================================================================
# JsonTranscriptFormatter
# ============================================================================


class TestJsonTranscriptFormatter:
    def test_empty_transcript_returns_empty_array(self):
        result = JsonTranscriptFormatter().format(_transcript())
        assert json.loads(result) == []

    def test_single_exchange_serialized(self):
        ex = _make_exchange(request=_user("Hello"), request_at=T0)
        data = json.loads(JsonTranscriptFormatter().format(_transcript(ex)))
        assert len(data) == 1
        assert data[0]["request"]["text"] == "Hello"

    def test_multiple_exchanges_sorted_by_request_at(self):
        e1 = _make_exchange(request=_user("Second"), request_at=T2)
        e2 = _make_exchange(request=_user("First"), request_at=T0)
        data = json.loads(JsonTranscriptFormatter().format(_transcript(e1, e2)))
        assert data[0]["request"]["text"] == "First"
        assert data[1]["request"]["text"] == "Second"

    def test_responses_included(self):
        ex = _make_exchange(
            request=_user("Hi"),
            responses=[_agent("Hey")],
            request_at=T0,
            response_at=T1,
        )
        data = json.loads(JsonTranscriptFormatter().format(_transcript(ex)))
        assert data[0]["responses"][0]["text"] == "Hey"

    def test_error_field_serialized(self):
        ex = _make_exchange(request=_user("Hi"), request_at=T0, error="timeout")
        data = json.loads(JsonTranscriptFormatter().format(_transcript(ex)))
        assert data[0]["error"] == "timeout"

    def test_model_dump_args_forwarded(self):
        ex = _make_exchange(request_at=T0)
        data = json.loads(
            JsonTranscriptFormatter(model_dump_args={"exclude_none": True}).format(
                _transcript(ex)
            )
        )
        # With exclude_none, the null request field should be absent
        assert "request" not in data[0]

    def test_callable_returns_same_as_format(self):
        fmt = JsonTranscriptFormatter()
        t = _transcript()
        assert fmt(t) == fmt.format(t)

    def test_satisfies_transcript_formatter_protocol(self):
        fmt: TranscriptFormatter = JsonTranscriptFormatter()
        assert isinstance(fmt.format(_transcript()), str)


# ============================================================================
# ActivityTranscriptFormatter
# ============================================================================


class TestActivityTranscriptFormatter:
    def test_empty_transcript_returns_empty_array(self):
        result = ActivityTranscriptFormatter().format(_transcript())
        assert json.loads(result) == []

    def test_request_activity_included(self):
        ex = _make_exchange(request=_user("Hello"), request_at=T0)
        data = json.loads(ActivityTranscriptFormatter().format(_transcript(ex)))
        assert len(data) == 1
        assert data[0]["text"] == "Hello"

    def test_request_then_responses_in_order(self):
        ex = _make_exchange(
            request=_user("Hi"),
            responses=[_agent("Hey"), _agent("How are you?")],
            request_at=T0,
            response_at=T1,
        )
        data = json.loads(ActivityTranscriptFormatter().format(_transcript(ex)))
        assert [d["text"] for d in data] == ["Hi", "Hey", "How are you?"]

    def test_exchange_with_no_request(self):
        ex = _make_exchange(responses=[_agent("Proactive")], response_at=T0)
        data = json.loads(ActivityTranscriptFormatter().format(_transcript(ex)))
        assert len(data) == 1
        assert data[0]["text"] == "Proactive"

    def test_exchange_with_no_responses(self):
        ex = _make_exchange(request=_user("Silent"), request_at=T0)
        data = json.loads(ActivityTranscriptFormatter().format(_transcript(ex)))
        assert len(data) == 1
        assert data[0]["text"] == "Silent"

    def test_multiple_exchanges_sorted_by_request_at(self):
        e1 = _make_exchange(request=_user("Second"), request_at=T2)
        e2 = _make_exchange(request=_user("First"), request_at=T0)
        data = json.loads(ActivityTranscriptFormatter().format(_transcript(e1, e2)))
        assert data[0]["text"] == "First"
        assert data[1]["text"] == "Second"

    def test_model_dump_args_forwarded(self):
        ex = _make_exchange(request=_user("Hi"), request_at=T0)
        data = json.loads(
            ActivityTranscriptFormatter(model_dump_args={"exclude_none": True}).format(
                _transcript(ex)
            )
        )
        assert "id" not in data[0]  # id is None by default and excluded

    def test_callable_returns_same_as_format(self):
        fmt = ActivityTranscriptFormatter()
        t = _transcript()
        assert fmt(t) == fmt.format(t)

    def test_satisfies_transcript_formatter_protocol(self):
        fmt: TranscriptFormatter = ActivityTranscriptFormatter()
        assert isinstance(fmt.format(_transcript()), str)


# ============================================================================
# ConversationTranscriptFormatter
# ============================================================================


class TestConversationTranscriptFormatter:
    def test_empty_transcript_returns_empty_string(self):
        assert ConversationTranscriptFormatter().format(_transcript()) == ""

    def test_user_message_labeled_you(self):
        ex = Exchange(request=_user("Hello there"), request_at=T0, responses=[])
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "You: Hello there" in result

    def test_non_user_message_labeled_agent(self):
        ex = Exchange(responses=[_agent("Hi back!")], response_at=T1)
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "Agent: Hi back!" in result

    def test_activity_without_from_property_labeled_agent(self):
        ex = Exchange(
            request=Activity.model_validate(
                {"type": ActivityTypes.message, "text": "No from"}
            ),
            request_at=T0,
            responses=[],
        )
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "Agent: No from" in result

    def test_error_exchange_shows_error_marker(self):
        ex = Exchange(
            request=_user("Hi"), request_at=T0, responses=[], error="Connection refused"
        )
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "[X] Error: Connection refused" in result

    def test_non_message_activity_shows_type_marker(self):
        typing_act = _make_activity(type="typing", role="user")
        ex = Exchange(request=typing_act, request_at=T0, responses=[])
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "--- You [typing] ---" in result

    def test_timestamp_in_output(self):
        ex = Exchange(request=_user("Hello"), request_at=T0, responses=[])
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "[10:00:00.000]" in result

    def test_empty_message_text_shows_placeholder(self):
        ex = Exchange(
            request=Activity.model_validate({"type": ActivityTypes.message}),
            request_at=T0,
            responses=[],
        )
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        assert "(empty message)" in result

    def test_multiple_exchanges_sorted_chronologically(self):
        e1 = Exchange(request=_user("Second"), request_at=T2, responses=[])
        e2 = Exchange(request=_user("First"), request_at=T0, responses=[])
        result = ConversationTranscriptFormatter().format(_transcript(e1, e2))
        assert result.index("First") < result.index("Second")

    def test_response_uses_activity_timestamp_when_set(self):
        res = _agent("At T2", timestamp=T2)
        ex = Exchange(responses=[res], response_at=T1)
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        # T2 is 10:00:02.500
        assert "[10:00:02.500]" in result

    def test_response_falls_back_to_exchange_response_at(self):
        res = Activity.model_validate({"type": ActivityTypes.message, "text": "No ts"})
        ex = Exchange(responses=[res], response_at=T1)
        result = ConversationTranscriptFormatter().format(_transcript(ex))
        # Falls back to T1 = 10:00:01.234
        assert "[10:00:01.234]" in result

    def test_callable_returns_same_as_format(self):
        fmt = ConversationTranscriptFormatter()
        t = _transcript()
        assert fmt(t) == fmt.format(t)

    def test_satisfies_transcript_formatter_protocol(self):
        fmt: TranscriptFormatter = ConversationTranscriptFormatter()
        assert isinstance(fmt.format(_transcript()), str)


# ============================================================================
# print_json / print_conversation / print_activities
# ============================================================================


class TestPrintFunctions:
    def test_print_json_outputs_valid_json(self, capsys):
        ex = _make_exchange(request=_user("Hi"), request_at=T0)
        print_json(_transcript(ex))
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert len(data) == 1

    def test_print_json_empty_transcript(self, capsys):
        print_json(_transcript())
        assert capsys.readouterr().out.strip() == "[]"

    def test_print_conversation_includes_label(self, capsys):
        ex = Exchange(request=_user("Hello!"), request_at=T0, responses=[])
        print_conversation(_transcript(ex))
        assert "You: Hello!" in capsys.readouterr().out

    def test_print_conversation_empty_transcript(self, capsys):
        print_conversation(_transcript())
        assert capsys.readouterr().out.strip() == ""

    def test_print_activities_outputs_valid_json(self, capsys):
        ex = _make_exchange(request=_user("Test"), request_at=T0)
        print_activities(_transcript(ex))
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert data[0]["text"] == "Test"

    def test_print_activities_empty_transcript(self, capsys):
        print_activities(_transcript())
        assert capsys.readouterr().out.strip() == "[]"

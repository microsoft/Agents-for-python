# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for transcript formatting and logging utilities."""

import pytest
from datetime import datetime, timedelta, timezone

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core import Transcript, Exchange
from microsoft_agents.testing.transcript_formatter import (
    DetailLevel,
    TimeFormat,
    TranscriptFormatter,
    ActivityTranscriptFormatter,
    ConversationTranscriptFormatter,
    print_conversation,
    print_activities,
    _print_messages,
    _exchange_sort_key,
    _format_timestamp,
    _format_relative_time,
    _get_transcript_start_time,
    _is_error_exchange,
    DEFAULT_ACTIVITY_FIELDS,
    EXTENDED_ACTIVITY_FIELDS,
)


# ============================================================================
# Test helpers
# ============================================================================


def _make_activity(
    type: str = ActivityTypes.message,
    text: str | None = None,
    from_id: str | None = None,
    from_name: str | None = None,
    recipient_id: str | None = None,
    recipient_name: str | None = None,
    **kwargs,
) -> Activity:
    """Create an Activity with common defaults."""
    data = {"type": type, **kwargs}
    if text is not None:
        data["text"] = text
    if from_id or from_name:
        data["from_property"] = {
            **({"id": from_id} if from_id else {}),
            **({"name": from_name} if from_name else {}),
        }
    if recipient_id or recipient_name:
        data["recipient"] = {
            **({"id": recipient_id} if recipient_id else {}),
            **({"name": recipient_name} if recipient_name else {}),
        }
    return Activity.model_validate(data)


def _make_exchange(
    request_text: str | None = "Hello",
    response_texts: list[str] | None = None,
    request_at: datetime | None = None,
    response_at: datetime | None = None,
    status_code: int | None = 200,
    error: str | None = None,
    body: str | None = None,
    request_type: str = ActivityTypes.message,
) -> Exchange:
    """Create an Exchange with sensible defaults."""
    request = _make_activity(
        type=request_type,
        text=request_text,
        from_id="user-1",
        from_name="User",
    ) if request_text is not None or request_type != ActivityTypes.message else None

    responses = []
    if response_texts:
        for rt in response_texts:
            responses.append(
                _make_activity(
                    text=rt,
                    from_id="agent-1",
                    from_name="Agent",
                )
            )

    return Exchange(
        request=request,
        request_at=request_at,
        response_at=response_at,
        status_code=status_code,
        responses=responses,
        error=error,
        body=body,
    )


def _make_transcript(exchanges: list[Exchange]) -> Transcript:
    """Create a Transcript with pre-recorded exchanges."""
    t = Transcript()
    for ex in exchanges:
        t.record(ex)
    return t


T0 = datetime(2026, 2, 6, 10, 0, 0, 0)
T1 = T0 + timedelta(seconds=1, milliseconds=234)
T2 = T0 + timedelta(seconds=2, milliseconds=500)
T3 = T0 + timedelta(seconds=5)


# ============================================================================
# Helper function tests
# ============================================================================


class TestExchangeSortKey:
    """Tests for _exchange_sort_key."""

    def test_sort_by_request_at(self):
        e1 = _make_exchange(request_at=T2)
        e2 = _make_exchange(request_at=T0)
        sorted_list = sorted([e1, e2], key=_exchange_sort_key)
        assert sorted_list[0].request_at == T0
        assert sorted_list[1].request_at == T2

    def test_falls_back_to_response_at_when_request_at_is_none(self):
        e = Exchange(response_at=T1, responses=[])
        key = _exchange_sort_key(e)
        assert key == (T1,)

    def test_uses_datetime_min_when_both_none(self):
        e = Exchange(responses=[])
        key = _exchange_sort_key(e)
        assert key == (datetime.min,)

    def test_handles_timezone_aware_datetimes(self):
        aware = T0.replace(tzinfo=timezone.utc)
        e = _make_exchange(request_at=aware)
        key = _exchange_sort_key(e)
        # Should strip tzinfo for comparison
        assert key == (T0,)


class TestFormatTimestamp:
    """Tests for _format_timestamp."""

    def test_formats_datetime(self):
        dt = datetime(2026, 2, 6, 14, 30, 45, 123456)
        result = _format_timestamp(dt)
        assert result == "14:30:45.123"

    def test_returns_placeholder_for_none(self):
        assert _format_timestamp(None) == "??:??.???"

    def test_truncates_microseconds_to_milliseconds(self):
        dt = datetime(2026, 1, 1, 0, 0, 0, 999999)
        result = _format_timestamp(dt)
        assert result == "00:00:00.999"


class TestFormatRelativeTime:
    """Tests for _format_relative_time."""

    def test_elapsed_format(self):
        result = _format_relative_time(T1, T0, TimeFormat.ELAPSED)
        assert result == "1.234s"

    def test_relative_format_positive(self):
        result = _format_relative_time(T1, T0, TimeFormat.RELATIVE)
        assert result == "+1.234s"

    def test_relative_format_negative(self):
        result = _format_relative_time(T0, T1, TimeFormat.RELATIVE)
        assert result.startswith("-")

    def test_returns_placeholder_when_dt_is_none(self):
        assert _format_relative_time(None, T0) == "?.???s"

    def test_returns_placeholder_when_start_is_none(self):
        assert _format_relative_time(T0, None) == "?.???s"

    def test_handles_mixed_tz_aware_and_naive(self):
        aware = T1.replace(tzinfo=timezone.utc)
        result = _format_relative_time(aware, T0, TimeFormat.ELAPSED)
        assert result == "1.234s"


class TestGetTranscriptStartTime:
    """Tests for _get_transcript_start_time."""

    def test_returns_earliest_request_at(self):
        exchanges = [
            _make_exchange(request_at=T2),
            _make_exchange(request_at=T0),
            _make_exchange(request_at=T1),
        ]
        result = _get_transcript_start_time(exchanges)
        assert result == T0

    def test_returns_none_when_no_timestamps(self):
        exchanges = [Exchange(responses=[])]
        assert _get_transcript_start_time(exchanges) is None

    def test_returns_none_for_empty_list(self):
        assert _get_transcript_start_time([]) is None


class TestIsErrorExchange:
    """Tests for _is_error_exchange."""

    def test_error_field_is_error(self):
        e = _make_exchange(error="Connection refused")
        assert _is_error_exchange(e) is True

    def test_status_400_is_error(self):
        e = _make_exchange(status_code=400)
        assert _is_error_exchange(e) is True

    def test_status_500_is_error(self):
        e = _make_exchange(status_code=500)
        assert _is_error_exchange(e) is True

    def test_status_200_is_not_error(self):
        e = _make_exchange(status_code=200)
        assert _is_error_exchange(e) is False

    def test_no_error_no_status_is_not_error(self):
        e = Exchange(responses=[])
        assert _is_error_exchange(e) is False


# ============================================================================
# ActivityTranscriptFormatter tests
# ============================================================================


class TestActivityTranscriptFormatter:
    """Tests for ActivityTranscriptFormatter."""

    def test_default_fields(self):
        fmt = ActivityTranscriptFormatter()
        assert fmt.fields == DEFAULT_ACTIVITY_FIELDS

    def test_custom_fields(self):
        fmt = ActivityTranscriptFormatter(fields=["type", "text"])
        assert fmt.fields == ["type", "text"]

    def test_format_empty_transcript(self):
        fmt = ActivityTranscriptFormatter()
        transcript = _make_transcript([])
        result = fmt.format(transcript)
        assert result == ""

    def test_format_single_exchange_standard(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)

        assert "=== Exchange ===" in result
        assert "SENT:" in result
        assert "RECV:" in result
        assert "Hi" in result
        assert "Hello!" in result

    def test_format_shows_selected_fields(self):
        exchange = _make_exchange(
            request_text="Test",
            response_texts=["Reply"],
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter(fields=["type", "text"])
        result = fmt.format(transcript)

        assert "type:" in result
        assert "text:" in result
        assert "Test" in result

    def test_format_detailed_shows_timestamp(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter(detail=DetailLevel.DETAILED)
        result = fmt.format(transcript)

        assert "Exchange [" in result
        assert "Latency:" in result

    def test_format_detailed_clock_time(self):
        exchange = _make_exchange(
            request_text="Hi",
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=TimeFormat.CLOCK,
        )
        result = fmt.format(transcript)
        assert "10:00:00.000" in result

    def test_format_detailed_elapsed_time(self):
        exchange = _make_exchange(
            request_text="Hi",
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=TimeFormat.ELAPSED,
        )
        result = fmt.format(transcript)
        assert "0.000s" in result

    def test_format_detailed_relative_time(self):
        e1 = _make_exchange(request_text="A", request_at=T0, response_at=T1)
        e2 = _make_exchange(request_text="B", request_at=T2, response_at=T3)
        transcript = _make_transcript([e1, e2])
        fmt = ActivityTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=TimeFormat.RELATIVE,
        )
        result = fmt.format(transcript)
        assert "+0.000s" in result
        assert "+2.500s" in result

    def test_format_full_shows_iso_timestamps(self):
        exchange = _make_exchange(
            request_text="Hi",
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter(detail=DetailLevel.FULL)
        result = fmt.format(transcript)

        assert "Request at:" in result
        assert "Response at:" in result
        assert T0.isoformat() in result
        assert T1.isoformat() in result

    def test_format_shows_status_code(self):
        exchange = _make_exchange(request_text="Hi", status_code=200)
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)
        assert "Status: 200" in result

    def test_format_flags_error_status(self):
        exchange = _make_exchange(request_text="Hi", status_code=500)
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)
        assert "ERROR" in result

    def test_format_shows_error_message(self):
        exchange = _make_exchange(
            request_text="Hi",
            error="Connection refused",
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)
        assert "Connection refused" in result

    def test_format_multiple_exchanges_sorted_by_time(self):
        e1 = _make_exchange(request_text="Second", request_at=T2)
        e2 = _make_exchange(request_text="First", request_at=T0)
        transcript = _make_transcript([e1, e2])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)

        idx_first = result.index("First")
        idx_second = result.index("Second")
        assert idx_first < idx_second

    def test_format_multiple_responses(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!", "How are you?"],
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)

        assert "Hello!" in result
        assert "How are you?" in result

    def test_select_returns_all_exchanges(self):
        e1 = _make_exchange(request_text="A")
        e2 = _make_exchange(request_text="B", status_code=500, error="fail")
        transcript = _make_transcript([e1, e2])
        fmt = ActivityTranscriptFormatter()
        selected = fmt._select(transcript)
        assert len(selected) == 2

    def test_format_exchange_without_request(self):
        """Exchange with no request (e.g., proactive message)."""
        exchange = Exchange(
            response_at=T0,
            responses=[_make_activity(text="Proactive!")],
        )
        transcript = _make_transcript([exchange])
        fmt = ActivityTranscriptFormatter()
        result = fmt.format(transcript)
        assert "Proactive!" in result

    def test_latency_shown_only_in_detailed_modes(self):
        exchange = _make_exchange(
            request_text="Hi",
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])

        standard = ActivityTranscriptFormatter(detail=DetailLevel.STANDARD)
        assert "Latency:" not in standard.format(transcript)

        detailed = ActivityTranscriptFormatter(detail=DetailLevel.DETAILED)
        assert "Latency:" in detailed.format(transcript)


# ============================================================================
# ConversationTranscriptFormatter tests
# ============================================================================


class TestConversationTranscriptFormatter:
    """Tests for ConversationTranscriptFormatter."""

    def test_format_empty_transcript(self):
        fmt = ConversationTranscriptFormatter()
        transcript = _make_transcript([])
        result = fmt.format(transcript)
        assert result == ""

    def test_format_simple_conversation(self):
        exchange = _make_exchange(
            request_text="Hello",
            response_texts=["Hi there!"],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter()
        result = fmt.format(transcript)

        assert "You: Hello" in result
        assert "Agent: Hi there!" in result

    def test_custom_labels(self):
        exchange = _make_exchange(
            request_text="Hey",
            response_texts=["Hi!"],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(
            user_label="Human",
            agent_label="Bot",
        )
        result = fmt.format(transcript)

        assert "Human: Hey" in result
        assert "Bot: Hi!" in result

    def test_hides_non_message_activities_by_default(self):
        exchange = _make_exchange(
            request_text=None,
            request_type="typing",
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter()
        result = fmt.format(transcript)
        assert "typing" not in result

    def test_shows_non_message_activities_when_enabled(self):
        exchange = Exchange(
            request=_make_activity(type="typing"),
            responses=[],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(show_other_types=True)
        result = fmt.format(transcript)
        assert "typing" in result

    def test_show_other_types_minimal_format(self):
        exchange = Exchange(
            request=_make_activity(type="typing"),
            responses=[],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(
            show_other_types=True,
            detail=DetailLevel.MINIMAL,
        )
        result = fmt.format(transcript)
        assert "--- [typing] ---" in result

    def test_show_other_types_standard_format(self):
        exchange = Exchange(
            request=_make_activity(type="typing"),
            responses=[],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(
            show_other_types=True,
            detail=DetailLevel.STANDARD,
        )
        result = fmt.format(transcript)
        assert "sent [typing] activity" in result

    def test_detailed_shows_timestamps(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(detail=DetailLevel.DETAILED)
        result = fmt.format(transcript)
        assert "[" in result  # timestamp bracket
        assert "You:" in result

    def test_detailed_shows_latency(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(detail=DetailLevel.DETAILED)
        result = fmt.format(transcript)
        assert "ms)" in result

    def test_full_shows_header_and_footer(self):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(detail=DetailLevel.FULL)
        result = fmt.format(transcript)

        assert "Conversation Log" in result
        assert "Total exchanges: 1" in result

    def test_full_shows_error_body(self):
        exchange = _make_exchange(
            request_text="Hi",
            status_code=500,
            body='{"error": "Internal Server Error"}',
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(detail=DetailLevel.FULL)
        result = fmt.format(transcript)
        assert "HTTP 500" in result
        assert "Body:" in result

    def test_shows_error_exchanges(self):
        exchange = _make_exchange(
            request_text="Hi",
            error="Connection refused",
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(show_errors=True)
        result = fmt.format(transcript)
        assert "Connection refused" in result

    def test_hides_error_exchanges_when_disabled(self):
        exchange = _make_exchange(
            request_text="Hi",
            error="Connection refused",
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(show_errors=False)
        # Error exchange is filtered out by _select
        selected = fmt._select(transcript)
        assert len(selected) == 0

    def test_format_multiple_exchanges_sorted(self):
        e1 = _make_exchange(request_text="Second", request_at=T2, response_texts=["R2"])
        e2 = _make_exchange(request_text="First", request_at=T0, response_texts=["R1"])
        transcript = _make_transcript([e1, e2])
        fmt = ConversationTranscriptFormatter()
        result = fmt.format(transcript)

        idx_first = result.index("First")
        idx_second = result.index("Second")
        assert idx_first < idx_second

    def test_empty_message_text(self):
        exchange = _make_exchange(request_text=None, request_type=ActivityTypes.message)
        # Force a message-type request with no text
        exchange.request = _make_activity(type=ActivityTypes.message, text=None)
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter()
        result = fmt.format(transcript)
        assert "(empty message)" in result

    def test_clock_time_format(self):
        exchange = _make_exchange(
            request_text="Hi",
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        fmt = ConversationTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=TimeFormat.CLOCK,
        )
        result = fmt.format(transcript)
        assert "10:00:00.000" in result

    def test_elapsed_time_format(self):
        e1 = _make_exchange(request_text="A", request_at=T0, response_texts=["R1"])
        e2 = _make_exchange(request_text="B", request_at=T1, response_texts=["R2"])
        transcript = _make_transcript([e1, e2])
        fmt = ConversationTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=TimeFormat.ELAPSED,
        )
        result = fmt.format(transcript)
        assert "0.000s" in result
        assert "1.234s" in result


# ============================================================================
# Convenience function tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for print_conversation, print_activities, and _print_messages."""

    def test_print_conversation(self, capsys):
        exchange = _make_exchange(request_text="Hi", response_texts=["Hello!"])
        transcript = _make_transcript([exchange])
        print_conversation(transcript)
        captured = capsys.readouterr()
        assert "You: Hi" in captured.out
        assert "Agent: Hello!" in captured.out

    def test_print_conversation_with_detail(self, capsys):
        exchange = _make_exchange(
            request_text="Hi",
            response_texts=["Hello!"],
            request_at=T0,
            response_at=T1,
        )
        transcript = _make_transcript([exchange])
        print_conversation(transcript, detail=DetailLevel.FULL)
        captured = capsys.readouterr()
        assert "Conversation Log" in captured.out

    def test_print_conversation_with_other_types(self, capsys):
        exchange = Exchange(
            request=_make_activity(type="typing"),
            responses=[],
        )
        transcript = _make_transcript([exchange])
        print_conversation(transcript, show_other_types=True)
        captured = capsys.readouterr()
        assert "typing" in captured.out

    def test_print_activities(self, capsys):
        exchange = _make_exchange(request_text="Hi", response_texts=["Hello!"])
        transcript = _make_transcript([exchange])
        print_activities(transcript)
        captured = capsys.readouterr()
        assert "=== Exchange ===" in captured.out
        assert "SENT:" in captured.out

    def test_print_activities_custom_fields(self, capsys):
        exchange = _make_exchange(request_text="Hi", response_texts=["Hello!"])
        transcript = _make_transcript([exchange])
        print_activities(transcript, fields=["type"])
        captured = capsys.readouterr()
        assert "type:" in captured.out

    def test_legacy_print_messages(self, capsys):
        exchange = _make_exchange(request_text="Hi", response_texts=["Hello!"])
        transcript = _make_transcript([exchange])
        _print_messages(transcript)
        captured = capsys.readouterr()
        assert "You: Hi" in captured.out


# ============================================================================
# TranscriptFormatter base class tests
# ============================================================================


class TestTranscriptFormatterBase:
    """Tests for the abstract TranscriptFormatter."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            TranscriptFormatter()

    def test_format_delegates_to_subclass(self):
        """Concrete subclass gets called correctly via format()."""

        class Reverse(TranscriptFormatter):
            def _select(self, transcript):
                return transcript.history()

            def _format_exchange(self, exchange):
                return (exchange.request.text or "")[::-1]

        exchange = _make_exchange(request_text="abcd")
        transcript = _make_transcript([exchange])
        fmt = Reverse()
        assert fmt.format(transcript) == "dcba"

    def test_print_writes_to_stdout(self, capsys):
        class Simple(TranscriptFormatter):
            def _select(self, transcript):
                return transcript.history()

            def _format_exchange(self, exchange):
                return "OK"

        transcript = _make_transcript([_make_exchange()])
        Simple().print(transcript)
        captured = capsys.readouterr()
        assert "OK" in captured.out


# ============================================================================
# Enum value tests
# ============================================================================


class TestEnums:
    """Tests that enum values are stable."""

    def test_detail_levels(self):
        assert DetailLevel.MINIMAL.value == "minimal"
        assert DetailLevel.STANDARD.value == "standard"
        assert DetailLevel.DETAILED.value == "detailed"
        assert DetailLevel.FULL.value == "full"

    def test_time_formats(self):
        assert TimeFormat.CLOCK.value == "clock"
        assert TimeFormat.RELATIVE.value == "relative"
        assert TimeFormat.ELAPSED.value == "elapsed"

    def test_default_activity_fields_include_essentials(self):
        assert "type" in DEFAULT_ACTIVITY_FIELDS
        assert "text" in DEFAULT_ACTIVITY_FIELDS

    def test_extended_fields_superset_of_default(self):
        for field in DEFAULT_ACTIVITY_FIELDS:
            assert field in EXTENDED_ACTIVITY_FIELDS

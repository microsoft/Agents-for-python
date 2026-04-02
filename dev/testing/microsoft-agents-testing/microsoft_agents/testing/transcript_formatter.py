# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript formatting and logging utilities.

Provides formatters for converting Transcript objects into human-readable
text representations for debugging and logging purposes.
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime

from microsoft_agents.activity import Activity, ActivityTypes

from .core import Transcript, Exchange


class DetailLevel(Enum):
    """Level of detail for transcript output."""
    MINIMAL = "minimal"      # Just the essential info
    STANDARD = "standard"    # Default, readable output
    DETAILED = "detailed"    # Include timing and latency info
    FULL = "full"            # Include everything including timeline


class TimeFormat(Enum):
    """Format for displaying timestamps."""
    CLOCK = "clock"          # Absolute time (HH:MM:SS.mmm)
    RELATIVE = "relative"    # Relative to start (e.g., +1.234s)
    ELAPSED = "elapsed"      # Elapsed seconds from start (e.g., 1.234s)


class TranscriptFormatter(ABC):
    """Abstract formatter for converting Transcripts to string output.
    
    Subclasses implement specific formatting strategies for different
    use cases (e.g., conversation view, debug view, JSON export).
    """

    @abstractmethod
    def _select(self, transcript: Transcript) -> list[Exchange]:
        """Filter the given Transcript according to specific criteria."""
        pass
    
    @abstractmethod
    def _format_exchange(self, exchange: Exchange) -> str:
        """Format a single Exchange into a string representation."""
        pass

    def format(self, transcript: Transcript) -> str:
        """Format the given Transcript into a string representation."""
        exchanges = sorted(self._select(transcript), key=_exchange_sort_key)
        formatted_exchanges = [self._format_exchange(e) for e in exchanges]
        return "\n".join(formatted_exchanges)
    
    def print(self, transcript: Transcript) -> None:
        """Print the formatted transcript to stdout."""
        print(self.format(transcript))


def _exchange_sort_key(exchange: Exchange) -> tuple:
    """Sort key for exchanges by request timestamp.
    
    Returns a tuple to handle naive vs aware datetime comparisons.
    """
    dt = exchange.request_at
    if dt is None:
        dt = exchange.response_at
    if dt is None:
        # Use min datetime for None values
        return (datetime.min,)
    # Convert to naive for consistent comparison
    naive_dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
    return (naive_dt,)


def _format_timestamp(dt: datetime | None) -> str:
    """Format a datetime for display."""
    if dt is None:
        return "??:??.???"
    return dt.strftime("%H:%M:%S.%f")[:-3]


def _format_relative_time(
    dt: datetime | None,
    start_time: datetime | None,
    time_format: TimeFormat = TimeFormat.ELAPSED,
) -> str:
    """Format a datetime relative to a start time."""
    if dt is None or start_time is None:
        return "?.???s"
    
    # Handle timezone-aware vs naive datetimes
    dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
    start_naive = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
    
    delta = (dt_naive - start_naive).total_seconds()
    
    if time_format == TimeFormat.RELATIVE:
        return f"+{delta:.3f}s" if delta >= 0 else f"{delta:.3f}s"
    else:  # ELAPSED
        return f"{delta:.3f}s"


def _get_transcript_start_time(exchanges: list[Exchange]) -> datetime | None:
    """Get the earliest timestamp from a list of exchanges."""
    timestamps = []
    for ex in exchanges:
        if ex.request_at:
            timestamps.append(ex.request_at)
    
    if not timestamps:
        return None
    
    # Convert to naive for comparison
    naive_times = [
        (t.replace(tzinfo=None) if t.tzinfo else t, t)
        for t in timestamps
    ]
    return min(naive_times, key=lambda x: x[0])[1]


def _is_error_exchange(exchange: Exchange) -> bool:
    """Check if an exchange represents an error."""
    if exchange.error:
        return True
    if exchange.status_code and exchange.status_code >= 400:
        return True
    return False


# ============================================================================
# ActivityTranscriptFormatter - Shows all activities with selectable fields
# ============================================================================


# Default fields to show for activities (not too verbose)
DEFAULT_ACTIVITY_FIELDS = [
    "type",
    "text",
    "from_property",
    "recipient",
]

# Extended fields for more detailed output
EXTENDED_ACTIVITY_FIELDS = [
    "type",
    "id",
    "text",
    "from_property",
    "recipient",
    "conversation",
    "reply_to_id",
    "value",
]


class ActivityTranscriptFormatter(TranscriptFormatter):
    """Logs every activity sent and received with selectable fields.
    
    Provides detailed visibility into all activities in the transcript,
    with configurable field selection and detail levels.
    
    Example::
    
        logger = ActivityTranscriptFormatter(fields=["type", "text", "from_property"])
        logger.print(transcript)
        
        # With timing info
        logger = ActivityTranscriptFormatter(detail=DetailLevel.DETAILED)
        logger.print(transcript)
    """
    
    def __init__(
        self,
        fields: list[str] | None = None,
        detail: DetailLevel = DetailLevel.STANDARD,
        show_errors: bool = True,
        time_format: TimeFormat = TimeFormat.CLOCK,
    ):
        """Initialize the ActivityTranscriptFormatter.
        
        Args:
            fields: List of Activity field names to display. 
                    Defaults to DEFAULT_ACTIVITY_FIELDS.
            detail: Level of detail for output.
            show_errors: Whether to include error exchanges.
            time_format: How to display timestamps (CLOCK, RELATIVE, ELAPSED).
        """
        self.fields = fields or DEFAULT_ACTIVITY_FIELDS
        self.detail = detail
        self.show_errors = show_errors
        self.time_format = time_format
        self._start_time: datetime | None = None

    def _select(self, transcript: Transcript) -> list[Exchange]:
        """Select all exchanges from the transcript."""
        return transcript.history()

    def _format_activity(self, activity: Activity, direction: str) -> str:
        """Format a single activity with selected fields."""
        parts = [f"  {direction}:"]
        
        for field in self.fields:
            value = getattr(activity, field, None)
            if value is not None:
                # Handle nested objects
                if hasattr(value, "id"):
                    value = f"id={value.id}"
                elif hasattr(value, "name"):
                    value = value.name
                elif hasattr(value, "model_dump"):
                    value = str(value.model_dump(exclude_none=True))
                parts.append(f"    {field}: {value}")
        
        return "\n".join(parts)

    def _format_exchange(self, exchange: Exchange) -> str:
        """Format a complete exchange with all activities."""
        lines = []
        
        # Header with timing
        if self.detail in (DetailLevel.DETAILED, DetailLevel.FULL):
            if self.time_format == TimeFormat.CLOCK:
                timestamp = _format_timestamp(exchange.request_at)
            else:
                timestamp = _format_relative_time(
                    exchange.request_at, self._start_time, self.time_format
                )
            lines.append(f"=== Exchange [{timestamp}] ===")
        else:
            lines.append("=== Exchange ===")
        
        # Request activity
        if exchange.request:
            lines.append(self._format_activity(exchange.request, "SENT"))
        
        # Status/Error info
        if exchange.status_code:
            status_str = f"  Status: {exchange.status_code}"
            if exchange.status_code >= 400:
                status_str += " ⚠ ERROR"
            lines.append(status_str)
        
        if exchange.error:
            lines.append(f"  [X] Error: {exchange.error}")
        
        # Latency info for detailed modes
        if self.detail in (DetailLevel.DETAILED, DetailLevel.FULL):
            if exchange.latency_ms is not None:
                lines.append(f"  Latency: {exchange.latency_ms:.1f}ms")
        
        # Timeline for full mode
        if self.detail == DetailLevel.FULL:
            if exchange.request_at:
                lines.append(f"  Request at: {exchange.request_at.isoformat()}")
            if exchange.response_at:
                lines.append(f"  Response at: {exchange.response_at.isoformat()}")
        
        # Response activities
        for response in exchange.responses:
            lines.append(self._format_activity(response, "RECV"))
        
        return "\n".join(lines)

    def format(self, transcript: Transcript) -> str:
        """Format the given Transcript into a string representation."""
        exchanges = sorted(self._select(transcript), key=_exchange_sort_key)
        
        # Calculate start time for relative formatting
        self._start_time = _get_transcript_start_time(exchanges)
        
        formatted_exchanges = [self._format_exchange(e) for e in exchanges]
        return "\n".join(formatted_exchanges)


# ============================================================================
# ConversationTranscriptFormatter - Focused on message text with compact output
# ============================================================================


class ConversationTranscriptFormatter(TranscriptFormatter):
    """Logs conversation messages in a chat-like format.
    
    Focuses on message activities and their text content, providing
    a clean conversation view. Optionally shows indicators for
    non-message activities without their full details.
    
    Example::
    
        logger = ConversationTranscriptFormatter()
        logger.print(transcript)
        
        # Show when non-message activities occur
        logger = ConversationTranscriptFormatter(show_other_types=True)
        logger.print(transcript)
        
        # With timing
        logger = ConversationTranscriptFormatter(detail=DetailLevel.DETAILED)
        logger.print(transcript)
    """
    
    def __init__(
        self,
        show_other_types: bool = False,
        detail: DetailLevel = DetailLevel.STANDARD,
        show_errors: bool = True,
        user_label: str = "You",
        agent_label: str = "Agent",
        time_format: TimeFormat = TimeFormat.CLOCK,
    ):
        """Initialize the ConversationTranscriptFormatter.
        
        Args:
            show_other_types: Show indicators for non-message activities.
            detail: Level of detail for output.
            show_errors: Whether to include error exchanges.
            user_label: Label for user messages (sent).
            agent_label: Label for agent messages (received).
            time_format: How to display timestamps (CLOCK, RELATIVE, ELAPSED).
        """
        self.show_other_types = show_other_types
        self.detail = detail
        self.show_errors = show_errors
        self.user_label = user_label
        self.agent_label = agent_label
        self.time_format = time_format
        self._start_time: datetime | None = None

    def _select(self, transcript: Transcript) -> list[Exchange]:
        """Select exchanges from the transcript."""
        exchanges = transcript.history()
        
        if not self.show_errors:
            exchanges = [e for e in exchanges if not _is_error_exchange(e)]
        
        return exchanges

    def _format_activity_line(
        self,
        activity: Activity,
        label: str,
        timestamp: datetime | None = None,
    ) -> str | None:
        """Format a single activity as a conversation line."""
        
        if activity.type == ActivityTypes.message:
            text = activity.text or "(empty message)"
            
            if self.detail in (DetailLevel.DETAILED, DetailLevel.FULL):
                if self.time_format == TimeFormat.CLOCK:
                    ts = _format_timestamp(timestamp)
                else:
                    ts = _format_relative_time(
                        timestamp, self._start_time, self.time_format
                    )
                return f"[{ts}] {label}: {text}"
            else:
                return f"{label}: {text}"
        
        elif self.show_other_types:
            # Show indicator for non-message activity
            if self.detail == DetailLevel.MINIMAL:
                return f"  --- [{activity.type}] ---"
            else:
                return f"  --- {label} sent [{activity.type}] activity ---"
        
        return None

    def _format_exchange(self, exchange: Exchange) -> str:
        """Format an exchange in conversation style."""
        lines = []
        
        # Handle errors first
        if _is_error_exchange(exchange):
            if self.show_errors:
                if exchange.error:
                    lines.append(f"[X] Error: {exchange.error}")
                elif exchange.status_code and exchange.status_code >= 400:
                    lines.append(f"[X] HTTP {exchange.status_code}")
                    if self.detail == DetailLevel.FULL and exchange.body:
                        lines.append(f"   Body: {exchange.body[:100]}...")
        
        # Request (user message)
        if exchange.request:
            line = self._format_activity_line(
                exchange.request,
                self.user_label,
                exchange.request_at,
            )
            if line:
                lines.append(line)
        
        # Show latency for detailed modes
        if self.detail in (DetailLevel.DETAILED, DetailLevel.FULL):
            if exchange.latency_ms is not None:
                lines.append(f"  ({exchange.latency_ms:.0f}ms)")
        
        # Responses (agent messages)
        for response in exchange.responses:
            line = self._format_activity_line(
                response,
                self.agent_label,
                exchange.response_at,
            )
            if line:
                lines.append(line)
        
        return "\n".join(lines) if lines else ""

    def format(self, transcript: Transcript) -> str:
        """Format the transcript with optional header."""
        exchanges = sorted(self._select(transcript), key=_exchange_sort_key)
        
        # Calculate start time for relative formatting
        self._start_time = _get_transcript_start_time(exchanges)
        
        lines = []
        
        if self.detail == DetailLevel.FULL:
            lines.append("+======================================+")
            lines.append("|          Conversation Log            |")
            lines.append("+======================================+")
            lines.append("")
        
        for exchange in exchanges:
            formatted = self._format_exchange(exchange)
            if formatted:
                lines.append(formatted)
        
        if self.detail == DetailLevel.FULL:
            lines.append("")
            lines.append(f"Total exchanges: {len(exchanges)}")
        
        return "\n".join(lines)


# ============================================================================
# Convenience functions
# ============================================================================


def print_conversation(
    transcript: Transcript,
    detail: DetailLevel = DetailLevel.STANDARD,
    show_other_types: bool = False,
) -> None:
    """Print transcript as a conversation.
    
    Convenience function for quick conversation viewing.
    
    Args:
        transcript: The transcript to print.
        detail: Level of detail.
        show_other_types: Show non-message activity indicators.
    """
    logger = ConversationTranscriptFormatter(
        detail=detail,
        show_other_types=show_other_types,
    )
    logger.print(transcript)


def print_activities(
    transcript: Transcript,
    fields: list[str] | None = None,
    detail: DetailLevel = DetailLevel.STANDARD,
) -> None:
    """Print transcript with all activity details.
    
    Convenience function for debugging.
    
    Args:
        transcript: The transcript to print.
        fields: Activity fields to show.
        detail: Level of detail.
    """
    logger = ActivityTranscriptFormatter(
        fields=fields,
        detail=detail,
    )
    logger.print(transcript)


# Legacy function for backward compatibility
def _print_messages(transcript: Transcript) -> None:
    """Legacy function to print transcript messages.
    
    Deprecated: Use print_conversation() instead.
    """
    print_conversation(transcript, detail=DetailLevel.STANDARD)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript formatting and logging utilities.

Provides formatters for converting Transcript objects into human-readable
text representations for debugging and logging purposes.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from microsoft_agents.activity import Activity, ActivityTypes

from .core import Transcript, Exchange

def _exchange_node_dt_sort_key(exchange: Exchange) -> datetime:
    """Get a sort key based on the exchange datetime."""
    dt = exchange.request_at
    if dt is None:
        dt = exchange.response_at
    return dt

def _print_messages(transcript: Transcript) -> None:

    exchanges = transcript.history()

    for exchange in exchanges:
        if exchange.request is not None and exchange.request.type == "message":
            print(f"User: {exchange.request.text}")
        for response in exchange.responses:
            if response.type == "message":
                print(f"Agent: {response.text}")

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

    @abstractmethod
    def format(self, transcript: Transcript) -> str:
        """Format the given Transcript into a string representation."""
        exchanges = sorted(self._select(transcript), key=_exchange_node_dt_sort_key)
        formatted_exchanges = [ self._format_exchange(e) for e in exchanges ]
        return "\n".join(formatted_exchanges)
    
class _ConversationTranscriptFormatter(TranscriptFormatter):
    """Basic formatter that includes all exchanges."""

    def _select(self, transcript: Transcript) -> list[Exchange]:
        return transcript.get_all()
    
    def _format_activity(self, activity: Activity) -> str:
        if activity.type == ActivityTypes.message:
            return activity.text
        return f"<Activity type={activity.type}>"
    
    def _format_exchange(self, exchange: Exchange) -> str:
        parts = []
        if exchange.request is not None:
            parts.append(f"User: {self._format_activity(exchange.request)}")
        if exchange.status_code is not None and exchange.status_code >= 300:
            parts.append(f"\t- send error: {exchange.response_at}: {exchange.status_code} - {exchange.body}")
        if exchange.responses is not None:
            for response in exchange.responses:
                parts.append(f"Agent: {self._format_activity(response)}")
        return "\n".join(parts)
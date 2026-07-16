# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from datetime import datetime

from .transcript_formatter import BaseTranscriptFormatter
from .utils import _format_timestamp

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core import Transcript, Exchange


@dataclass
class _ActivityObservation:
    """Represents an observation of an activity in the conversation."""

    activity: Activity
    at: datetime

    error: str | None = None

    @property
    def is_error(self) -> bool:
        """Check if the observation represents an error."""
        return self.error is not None


class ConversationTranscriptFormatter(BaseTranscriptFormatter):
    """Formats a transcript as a human-readable conversation string.

    Each activity is rendered on its own line as:
    ``[HH:MM:SS.mmm] You: <text>`` for user messages,
    ``[HH:MM:SS.mmm] Agent: <text>`` for agent messages, and
    ``[HH:MM:SS.mmm]   --- Agent [<type>] ---`` for non-message activity types.
    Errors are rendered as ``[HH:MM:SS.mmm] [X] Error: <message>``.
    Lines are sorted by activity timestamp.
    """

    def _get_exchange_observations(
        self, exchange: Exchange
    ) -> list[_ActivityObservation]:
        """Return observations for a single exchange, preserving request/response order."""
        obs = []
        if exchange.request:
            assert exchange.request_at is not None
            obs.append(
                _ActivityObservation(
                    activity=exchange.request,
                    at=exchange.request_at,
                    error=exchange.error,
                )
            )
        if exchange.responses:
            assert exchange.response_at is not None
            for response in exchange.responses:
                obs.append(
                    _ActivityObservation(
                        activity=response, at=response.timestamp or exchange.response_at
                    )
                )
        return obs

    def _get_observations(self, transcript: Transcript) -> list[_ActivityObservation]:
        """Collect and sort all observations across the full transcript by timestamp."""
        obs = []
        for exchange in transcript.history():
            obs.extend(self._get_exchange_observations(exchange))

        return sorted(obs, key=lambda o: o.at)

    def _format_exchange(self, exchange: Exchange) -> str:
        """Format a single exchange as newline-separated observation lines."""
        return "\n".join(
            self._format_observation(obs)
            for obs in self._get_exchange_observations(exchange)
        )

    def _format_observation(self, observation: _ActivityObservation) -> str:
        """Format a single activity observation as a timestamped conversation line."""
        ts = _format_timestamp(observation.at)

        if observation.is_error:
            return f"[{ts}] [X] Error: {observation.error}"

        activity = observation.activity
        role = activity.from_property.role if activity.from_property else None
        label = "You" if role == "user" else "Agent"

        if activity.type == ActivityTypes.message:
            text = activity.text or "(empty message)"
            return f"[{ts}] {label}: {text}"

        return f"[{ts}]   --- {label} [{activity.type}] ---"

    def format(self, transcript: Transcript) -> str:
        """Format a transcript as a conversation."""
        observations = self._get_observations(transcript)
        return "\n".join(self._format_observation(obs) for obs in observations)

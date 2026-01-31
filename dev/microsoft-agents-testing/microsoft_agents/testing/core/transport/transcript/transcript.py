# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .exchange import Exchange

class Transcript:
    """A transcript of exchanges."""

    def __init__(self, parent: Transcript | None = None):
        """Initialize the transcript."""
        self._parent: Transcript | None = parent
        self._children: list[Transcript] = []
        self._history: list[Exchange] = []

    def _add(self, exchange: Exchange) -> None:
        """Add an exchange to the transcript without propagating.
        
        :param exchange: The exchange to add.
        """
        self._history.append(exchange)

    def _propagate_up(self, exchange: Exchange) -> None:
        """Begin propagating an exchange up to the parent transcript.
        
        :param exchange: The exchange to propagate.
        """
        if self._parent:
            self._parent._add(exchange)
            self._parent._propagate_up(exchange)

    def _propagate_down(self, exchange: Exchange) -> None:
        """Begin propagating an exchange down to the child transcripts.
        
        :param exchange: The exchange to propagate.
        """
        for child in self._children:
            child._add(exchange)
            child._propagate_down(exchange)

    def clear(self) -> None:
        """Clear the transcript."""
        self._history = []

    def history(self) -> list[Exchange]:
        """Get the full history of exchanges."""
        return list(self._history)
    
    def get_root(self) -> Transcript:
        """Get the root transcript."""
        if self._parent is None:
            return self
        return self._parent.get_root()

    def record(self, exchange: Exchange) -> None:
        """Record an exchange in the transcript."""
        self._add(exchange)
        self._propagate_up(exchange)
        self._propagate_down(exchange)
    
    def child(self) -> Transcript:
        """Create a child transcript."""
        return Transcript(parent=self)
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript - A hierarchical record of agent interactions.

Provides a tree-structured collection of Exchanges that supports
parent-child relationships for organizing complex test scenarios.
"""

from __future__ import annotations
from typing import Iterator

from .exchange import Exchange


class Transcript:
    """A hierarchical transcript of exchanges with an agent.
    
    Transcripts support parent-child relationships, allowing exchanges
    to be recorded at multiple levels. Exchanges propagate up to parents
    and down to children, enabling both isolated and shared views.
    """

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
        c = Transcript(parent=self)
        self._children.append(c)
        return c
    
    def __len__(self) -> int:
        """Get the number of exchanges in the transcript."""
        return len(self._history)
    
    def __iter__(self) -> Iterator[Exchange]:
        """Iterate over the exchanges in the transcript."""
        return iter(self._history)
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .exchange import Exchange

class ExchangeNode:
    
    exchange: Exchange
    source: Transcript

class Transcript:
    def __init__(self, parent: Transcript | None = None):
        self._parent = parent
        self._nodes: list[ExchangeNode] = []
        self._cursor: int = 0

    def _record_node(self, node: ExchangeNode) -> None:
        """Record a node in this transcript and propagate to parent."""
        self._nodes.append(node)
        if self._parent:
            self._parent._record_node(node)

    def record(self, exchange: Exchange) -> None:
        """Record an exchange in the transcript."""
        node = ExchangeNode(exchange=exchange, source=self)
        self._record_node(node)
    
    def get_all(self) -> list[Exchange]:
        """All exchanges."""
        return [ node.exchange for node in self._nodes ]
    
    def get_new(self) -> list[Exchange]:
        """Get new and advance cursor."""
        result = [ node.exchange for node in self._nodes[self._cursor:] ]
        self._cursor = len(self._nodes)
        return result
    
    def child(self) -> Transcript:
        return Transcript(parent=self)

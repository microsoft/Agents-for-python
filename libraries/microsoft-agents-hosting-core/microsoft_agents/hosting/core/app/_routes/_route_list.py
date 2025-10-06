"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import heapq
from typing import Generic, Optional, TypeVar

from ..state.turn_state import TurnState

from .._type_defs import RouteSelector, RouteHandler
from ._route import _Route
from .route_rank import RouteRank

StateT = TypeVar("StateT", bound=TurnState)

class _RouteList(Generic[StateT]):
    _routes: list[_Route[StateT]]

    def __init__(
        self,
    ) -> None:
        # a min-heap where lower "values" indicate higher priority
        self._routes = []

    def add_route(self, route: _Route[StateT]) -> None:
        """Adds a route to the list."""
        heapq.heappush(self._routes, route)

    def __iter__(self):
        return iter(self._routes)

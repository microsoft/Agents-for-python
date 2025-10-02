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

    def add_route(
        self,
        route_selector: RouteSelector,
        route_handler: RouteHandler[StateT],
        is_invoke: bool = False,
        rank: RouteRank = RouteRank.DEFAULT,
        auth_handlers: Optional[list[str]] = None,
    ) -> None:
        """Add a route to the priority queue."""
        route = _Route(
            selector=route_selector,
            handler=route_handler,
            is_invoke=is_invoke,
            rank=rank,
            auth_handlers=auth_handlers or [],
        )

        heapq.heappush(self._routes, route)

    def __iter__(self):
        return iter(self._routes)

"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import heapq
from typing import Generic, Optional, TypeVar

from microsoft_agents.hosting.core import TurnState

from ..type_defs import RouteSelector, RouteHandler
from .route import Route
from .route_rank import RouteRank

StateT = TypeVar("StateT", bound=TurnState)

class RouteList(Generic[StateT]):
    _routes: list[Route[StateT]]
    
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
        auth_handlers: Optional[list[str]] = None
    ) -> None:
        """Add a route to the priority queue."""
        route = Route(
            selector=route_selector,
            handler=route_handler,
            is_invoke=is_invoke,
            rank=rank,
            auth_handlers=auth_handlers or []
        )

        heapq.heappush(self._routes, route)

    def get_routes(self) -> list[Route[StateT]]:
        """Get all routes in priority order."""
        return self._routes
"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Generic, Optional

from ..type_defs import RouteHandler, RouteSelector, StateT
from .route_rank import RouteRank

class Route(Generic[StateT]):
    selector: RouteSelector
    handler: RouteHandler[StateT]
    is_invoke: bool
    rank: RouteRank
    auth_handlers: list[str]

    def __init__(
        self,
        selector: RouteSelector,
        handler: RouteHandler[StateT],
        is_invoke: bool = False,
        rank: RouteRank = RouteRank.DEFAULT,
        auth_handlers: Optional[list[str]] = None,
    ) -> None:
        self.selector = selector
        self.handler = handler
        self.is_invoke = is_invoke
        self.rank = rank
        self.auth_handlers = auth_handlers or []

    def __lt__(self, other: Route) -> bool:
        return self.is_invoke < other.is_invoke or \
            (self.is_invoke == other.is_invoke and self.rank < other.rank)
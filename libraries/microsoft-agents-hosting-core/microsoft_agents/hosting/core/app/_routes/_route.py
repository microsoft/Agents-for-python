# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from ...turn_context import TurnContext
from .._type_defs import RouteHandler, RouteSelector
from ..state.turn_state import TurnState
from .route_rank import RouteRank


def _agentic_selector(selector: RouteSelector) -> RouteSelector:
    def wrapped_selector(context: TurnContext) -> bool:
        return context.activity.is_agentic_request() and selector(context)

    return wrapped_selector


StateT = TypeVar("StateT", bound=TurnState)


class _Route(Generic[StateT]):
    selector: RouteSelector
    handler: RouteHandler[StateT]
    _is_invoke: bool
    _rank: RouteRank
    auth_handlers: list[str]
    _is_agentic: bool

    def __init__(
        self,
        selector: RouteSelector,
        handler: RouteHandler[StateT],
        is_invoke: bool = False,
        rank: RouteRank = RouteRank.DEFAULT,
        auth_handlers: Optional[list[str]] = None,
        is_agentic: bool = False,
        **kwargs,
    ) -> None:
        
        if rank < 0 or rank > RouteRank.LAST:
            raise ValueError("Route rank must be between 0 and RouteRank.LAST (inclusive)")

        self.selector = selector
        self.handler = handler
        self._is_invoke = is_invoke
        self._rank = rank
        self._is_agentic = is_agentic
        self.auth_handlers = auth_handlers or []

    @property
    def is_invoke(self) -> bool:
        return self._is_invoke

    @property
    def rank(self) -> RouteRank:
        return self._rank

    @property
    def is_agentic(self) -> bool:
        return self._is_agentic

    @property
    def priority(self) -> list[int]:
        """Lower "values" indicate higher priority."""
        return [
            0 if self._is_invoke else 1,
            0 if self._is_agentic else 1,
            self._rank.value,
        ]

    def __lt__(self, other: _Route) -> bool:
        # built-in list ordering is a lexicographic comparison in Python
        return self.priority < other.priority

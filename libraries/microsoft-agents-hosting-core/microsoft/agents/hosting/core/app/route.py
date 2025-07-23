"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Generic, List, TypeVar

from microsoft.agents.hosting.core import TurnContext
from .state import TurnState

StateT = TypeVar("StateT", bound=TurnState)
RouteHandler = Callable[[TurnContext, StateT], Awaitable[None]]


class Route(Generic[StateT]):
    selector: Callable[[TurnContext], bool]
    handler: RouteHandler[StateT]
    is_invoke: bool

    def __init__(
        self,
        selector: Callable[[TurnContext], bool],
        handler: RouteHandler,
        is_invoke: bool = False,
        auth_handlers: List[str] = None,
    ) -> None:
        self.selector = selector
        self.handler = handler
        self.is_invoke = is_invoke
        self.auth_handlers = auth_handlers or []

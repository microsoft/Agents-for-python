# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Callable,
    TypeVar,
    Pattern,
    Protocol,
)

from microsoft_agents.hosting.core import TurnState

from .teams_turn_context import TeamsTurnContext

TeamsRouteSelector = Callable[[TeamsTurnContext], bool]

StateT = TypeVar("StateT", bound=TurnState)
RouteHandlerT = TypeVar("RouteHandlerT", bound=Callable)

CommandSelector = str | Pattern[str] | None

class _RouteDecorator(Protocol[RouteHandlerT]):
    def __call__(self, func: RouteHandlerT) -> RouteHandlerT: ...
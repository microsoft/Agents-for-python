# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared type aliases and protocols used across the Teams hosting sub-package."""

from typing import (
    Callable,
    TYPE_CHECKING,
    TypeVar,
    Pattern,
    Protocol,
)

from microsoft_agents.hosting.core import TurnState

if TYPE_CHECKING:
    from .teams_turn_context import TeamsTurnContext

TeamsRouteSelector = Callable[["TeamsTurnContext"], bool]

StateT = TypeVar("StateT", bound=TurnState)
_StateContra = TypeVar("_StateContra", bound=TurnState, contravariant=True)
RouteHandlerT = TypeVar("RouteHandlerT", bound=Callable)

CommandSelector = str | Pattern[str] | None


class _RouteDecorator(Protocol[RouteHandlerT]):
    """Protocol for a decorator that registers *func* as a route and returns it unchanged."""

    def __call__(self, func: RouteHandlerT) -> RouteHandlerT:
        """Register *func* as a route handler and return it.

        :param func: The handler to register.
        :return: The same handler, unmodified, so it can be used as a plain callable.
        """
        ...

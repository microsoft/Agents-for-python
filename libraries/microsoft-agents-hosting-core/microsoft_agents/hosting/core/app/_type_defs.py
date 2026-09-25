# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, TypeVar, Awaitable, Protocol

from ..turn_context import TurnContext
from .state import TurnState

RouteSelector = Callable[[TurnContext], bool]

StateT = TypeVar("StateT", bound=TurnState)
_StateContra = TypeVar("_StateContra", bound=TurnState, contravariant=True)
_RouteHandlerT = TypeVar("_RouteHandlerT", bound=Callable)


class _RouteDecorator(Protocol[_RouteHandlerT]):
    """Protocol for a decorator that registers *func* as a route and returns it unchanged."""

    def __call__(self, func: _RouteHandlerT) -> _RouteHandlerT:
        """Register *func* as a route handler and return it.

        :param func: The handler to register.
        :return: The same handler, unmodified, so it can be used as a plain callable.
        """
        ...


class RouteHandler(Protocol[StateT]):
    def __call__(self, context: TurnContext, state: StateT, /) -> Awaitable[None]: ...


class HandoffHandler(Protocol[StateT]):
    def __call__(
        self, context: TurnContext, state: StateT, handoff_data: str
    ) -> Awaitable[None]: ...

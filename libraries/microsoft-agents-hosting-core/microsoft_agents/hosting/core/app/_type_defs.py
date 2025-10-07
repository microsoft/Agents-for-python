# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, TypeVar, Awaitable, Protocol

from ..turn_context import TurnContext
from .state import TurnState

RouteSelector = Callable[[TurnContext], bool]

StateT = TypeVar("StateT", bound=TurnState)


class RouteHandler(Protocol[StateT]):
    def __call__(self, context: TurnContext, state: StateT) -> Awaitable[None]: ...

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import (
    Awaitable,
    Protocol,
)

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app._type_defs import (
    RouteHandler,
    HandoffHandler,
)

from .teams_turn_context import TeamsTurnContext
from .type_defs import StateT

class TeamsRouteHandler(Protocol[StateT]):
    def __call__(self, context: TeamsTurnContext, state: StateT) -> Awaitable[None]: ...

    @staticmethod
    def wrap(handler: TeamsRouteHandler[StateT]) -> RouteHandler[StateT]:
        async def __func(context: TurnContext, state: StateT) -> None:
            teams_context = TeamsTurnContext(context)
            await handler(teams_context, state)
        return __func
    
class TeamsHandoffHandler(Protocol[StateT]):
    def __call__(self, context: TeamsTurnContext, state: StateT, handoff_data: str) -> Awaitable[None]: ...

    @staticmethod
    def wrap(handler: TeamsHandoffHandler[StateT]) -> HandoffHandler[StateT]:
        async def __func(context: TurnContext, state: StateT, handoff_data: str) -> None:
            teams_context = TeamsTurnContext(context)
            await handler(teams_context, state, handoff_data)
        return __func
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import (
    Awaitable,
    Protocol,
)

from microsoft_agents.hosting.core import (
    RouteHandler,
    TurnContext,
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

# Meetings route handlers

# Message extension route handlers

# Messages route handler

class O365ConnectorCardActionHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: O365ConnectorCardActionQuery
        ) -> Awaitable[None]:
        ...

class ReadReceiptHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: dict
        ) -> Awaitable[None]:
        ...

# Teams Channels route handlers

class ChannelUpdateHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: Channel
        ) -> Awaitable[None]:
        ...

class TeamUpdateHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: Team
        ) -> Awaitable[None]:
        ...
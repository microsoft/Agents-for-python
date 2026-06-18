# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams-aware route and handoff handlers."""

from __future__ import annotations

from typing import (
    Awaitable,
    Protocol,
)

from microsoft_agents.hosting.core import AgentApplication, TurnContext
from microsoft_agents.hosting.core.app._type_defs import (
    RouteHandler,
    HandoffHandler,
)

from .teams_turn_context import TeamsTurnContext
from .type_defs import StateT


class TeamsRouteHandler(Protocol[StateT]):
    """Protocol for a Teams route handler that receives a :class:`TeamsTurnContext`."""

    def __call__(self, context: TeamsTurnContext, state: StateT) -> Awaitable[None]:
        """Handle a turn with Teams context.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        """
        ...

    @staticmethod
    def wrap(
        handler: TeamsRouteHandler[StateT], app: AgentApplication
    ) -> RouteHandler[StateT]:
        """Adapt a :class:`TeamsRouteHandler` into a plain :class:`RouteHandler`.

        Wraps *handler* so that the core routing engine (which passes a plain
        :class:`TurnContext`) receives a compatible callable.

        :param handler: The Teams-specific handler to wrap.
        :param app: The agent application handling the turn.
        :return: A :class:`RouteHandler` that upgrades the context before delegating.
        """

        async def __func(context: TurnContext, state: StateT) -> None:
            teams_context = TeamsTurnContext(context, app)
            await handler(teams_context, state)

        return __func


class TeamsHandoffHandler(Protocol[StateT]):
    """Protocol for a Teams handoff handler that receives handoff continuation data."""

    def __call__(
        self, context: TeamsTurnContext, state: StateT, handoff_data: str
    ) -> Awaitable[None]:
        """Handle a handoff activity with Teams context.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param handoff_data: Opaque continuation data from the handoff initiator.
        """
        ...

    @staticmethod
    def wrap(
        handler: TeamsHandoffHandler[StateT], app: AgentApplication
    ) -> HandoffHandler[StateT]:
        """Adapt a :class:`TeamsHandoffHandler` into a plain :class:`HandoffHandler`.

        :param handler: The Teams-specific handoff handler to wrap.
        :param app: The agent application handling the turn.
        :return: A :class:`HandoffHandler` that upgrades the context before delegating.
        """

        async def __func(
            context: TurnContext, state: StateT, handoff_data: str
        ) -> None:
            teams_context = TeamsTurnContext(context, app)
            await handler(teams_context, state, handoff_data)

        return __func

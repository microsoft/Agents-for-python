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
from .type_defs import _StateContra


class TeamsRouteHandler(Protocol[_StateContra]):
    """Protocol for a Teams route handler that receives a :class:`TeamsTurnContext`."""

    def __call__(
        self, context: TeamsTurnContext, state: _StateContra, /
    ) -> Awaitable[None]:
        """Handle a turn with Teams context.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        """
        ...


def wrap_teams_route_handler(
    handler: TeamsRouteHandler[_StateContra], app: AgentApplication
) -> RouteHandler[_StateContra]:
    """Adapt a :class:`TeamsRouteHandler` into a plain :class:`RouteHandler`.

    Wraps *handler* so that the core routing engine (which passes a plain
    :class:`TurnContext`) receives a compatible callable.

    :param handler: The Teams-specific handler to wrap.
    :param app: The agent application handling the turn.
    :return: A :class:`RouteHandler` that upgrades the context before delegating.
    """

    async def __func(context: TurnContext, state: _StateContra) -> None:
        teams_context = TeamsTurnContext(context, app)
        await handler(teams_context, state)

    return __func


class TeamsHandoffHandler(Protocol[_StateContra]):
    """Protocol for a Teams handoff handler that receives handoff continuation data."""

    def __call__(
        self, context: TeamsTurnContext, state: _StateContra, handoff_data: str, /
    ) -> Awaitable[None]:
        """Handle a handoff activity with Teams context.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param handoff_data: Opaque continuation data from the handoff initiator.
        """
        ...


def wrap_teams_handoff_handler(
    handler: TeamsHandoffHandler[_StateContra], app: AgentApplication
) -> HandoffHandler[_StateContra]:
    """Adapt a :class:`TeamsHandoffHandler` into a plain :class:`HandoffHandler`.

    :param handler: The Teams-specific handoff handler to wrap.
    :param app: The agent application handling the turn.
    :return: A :class:`HandoffHandler` that upgrades the context before delegating.
    """

    async def __func(
        context: TurnContext, state: _StateContra, handoff_data: str
    ) -> None:
        teams_context = TeamsTurnContext(context, app)
        await handler(teams_context, state, handoff_data)

    return __func

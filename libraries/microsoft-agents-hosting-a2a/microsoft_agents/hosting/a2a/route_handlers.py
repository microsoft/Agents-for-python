# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams-aware route and handoff handlers."""

from __future__ import annotations

from typing import (
    Awaitable,
    Protocol,
)

from microsoft_agents.hosting.core import AgentApplication, TurnContext
from microsoft_agents.hosting.core.app._type_defs import RouteHandler

from .a2a_turn_context import A2ATurnContext
from .type_defs import _StateContra


class A2ARouteHandler(Protocol[_StateContra]):
    """Protocol for a Teams route handler that receives a :class:`TeamsTurnContext`."""

    def __call__(
        self, context: TeamsTurnContext, state: _StateContra, /
    ) -> Awaitable[None]:
        """Handle a turn with Teams context.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        """
        ...


def wrap_a2a_route_handler(
    handler: A2ARouteHandler[_StateContra], app: AgentApplication
) -> RouteHandler[_StateContra]:
    """Adapt a :class:`TeamsRouteHandler` into a plain :class:`RouteHandler`.

    Wraps *handler* so that the core routing engine (which passes a plain
    :class:`TurnContext`) receives a compatible callable.

    :param handler: The Teams-specific handler to wrap.
    :param app: The agent application handling the turn.
    :return: A :class:`RouteHandler` that upgrades the context before delegating.
    """

    async def __func(context: TurnContext, state: _StateContra) -> None:
        a2a_context = A2ATurnContext(context, app)
        await handler(a2a_context, state)

    return __func
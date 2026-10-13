"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Protocol definitions for Slack-aware route handlers.
"""

from __future__ import annotations

from typing import Awaitable, Protocol

from microsoft_agents.hosting.core import AgentApplication, TurnContext
from microsoft_agents.hosting.core.app._type_defs import RouteHandler, _StateContra

from .slack_turn_context import SlackTurnContext


class SlackRouteHandler(Protocol[_StateContra]):
    """Protocol for a Slack route handler that receives a :class:`SlackTurnContext`."""

    def __call__(
        self, context: SlackTurnContext, state: _StateContra, /
    ) -> Awaitable[None]:
        """Handle a turn with Slack context.

        :param context: Slack-aware turn context.
        :param state: The current turn state.
        """
        ...


def wrap_slack_route_handler(
    handler: SlackRouteHandler[_StateContra], app: AgentApplication
) -> RouteHandler[_StateContra]:
    """Adapt a :class:`SlackRouteHandler` into a plain :class:`RouteHandler`.

    Wraps *handler* so that the core routing engine (which passes a plain
    :class:`TurnContext`) receives a compatible callable.

    :param handler: The Slack-specific handler to wrap.
    :param app: The agent application handling the turn.
    :return: A :class:`RouteHandler` that upgrades the context before delegating.
    """

    async def __func(context: TurnContext, state: _StateContra) -> None:
        slack_context = SlackTurnContext(context, app)
        await handler(slack_context, state)

    return __func

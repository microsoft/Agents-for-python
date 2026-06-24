# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams configuration (config/fetch, config/submit) invokes."""

from typing import Generic, Optional, overload

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.msteams._utils import _send_invoke_response

from .route_handlers import ConfigHandler


class Config(Generic[StateT]):
    """Route registration for Teams config invoke activities.

    Access via :attr:`TeamsAgentExtension.config`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def _create_decorator(
        self,
        name: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ConfigHandler[StateT]]:
        """Build a route decorator for a Teams configuration invoke name.

        :param name: The invoke activity name to match (e.g. ``"config/fetch"``).
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority rank.
        :return: A decorator that registers the handler.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == name
            )

        def __call(func: ConfigHandler[StateT]) -> ConfigHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                response = await func(teams_context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    @overload
    def fetch(self, handler: ConfigHandler[StateT]) -> ConfigHandler[StateT]: ...
    @overload
    def fetch(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ConfigHandler[StateT]]: ...
    def fetch(
        self,
        handler: Optional[ConfigHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ConfigHandler[StateT] | _RouteDecorator[ConfigHandler[StateT]]:
        """Register a handler for config/fetch invokes."""
        decorator = self._create_decorator(
            "config/fetch", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def submit(self, handler: ConfigHandler[StateT]) -> ConfigHandler[StateT]: ...
    @overload
    def submit(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ConfigHandler[StateT]]: ...
    def submit(
        self,
        handler: Optional[ConfigHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ConfigHandler[StateT] | _RouteDecorator[ConfigHandler[StateT]]:
        """Register a handler for config/submit invokes."""
        decorator = self._create_decorator(
            "config/submit", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Generic, Optional

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.teams._utils import _send_invoke_response

from .route_handlers import ConfigurationHandler

class Configuration(Generic[StateT]):

    def __init__(self, app: AgentApplication[StateT]):
        self._app = app

    def _create_decorator(
        self,
        name: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ConfigurationHandler[StateT]]:
        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == name
            )

        def __call(func: ConfigurationHandler[StateT]) -> ConfigurationHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
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

    def on_config_fetch(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ConfigurationHandler[StateT]]:
        """Register a handler for config/fetch invokes."""
        return self._create_decorator("config/fetch", auth_handlers=auth_handlers, rank=rank)
    
    def on_config_submit(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ConfigurationHandler[StateT]]:
        """Register a handler for config/submit invokes."""
        return self._create_decorator("config/submit", auth_handlers=auth_handlers, rank=rank)
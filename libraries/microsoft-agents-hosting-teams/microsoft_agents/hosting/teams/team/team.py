# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Callable,
    Generic,
    Optional
)

from microsoft_teams.api.models import Team

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.teams.route_handlers import TeamsRouteHandler
from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agetns.hosting.teams._utils import (
    _get_channel_event_type,
)

from .route_handlers import TeamUpdateHandler

def _get_team_data(context: TurnContext) -> Team:
    data = context.activity.channel_data
    if data is None:
        raise ValueError("Channel data is required")
    if isinstance(data, dict):
        return Team(**data)
    return Team.model_validate(data)

class Team(Generic[StateT]):

    def __init__(self, app: AgentApplication[StateT]):
        self._app = app

    def _create_decorator(
        self,
        event_type: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: TeamUpdateHandler[StateT]) -> TeamUpdateHandler[StateT]:

            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                team_data = _get_team_data(context)
                await func(teams_context, state, team_data)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func
        
        return __call


    def archived(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamArchived conversation update events."""
        return self._create_decorator(
            "teamArchived", auth_handlers=auth_handlers, rank=rank
        )

    def deleted(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamDeleted conversation update events."""
        return self._create_decorator(
            "teamDeleted", auth_handlers=auth_handlers, rank=rank
        )

    def hard_deleted(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamHardDeleted conversation update events."""
        return self._create_decorator(
            "teamHardDeleted", auth_handlers=auth_handlers, rank=rank
        )

    def renamed(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamRenamed conversation update events."""
        return self._create_decorator(
            "teamRenamed", auth_handlers=auth_handlers, rank=rank
        )

    def restored(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamRestored conversation update events."""
        return self._create_decorator(
            "teamRestored", auth_handlers=auth_handlers, rank=rank
        )

    def unarchived(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamUnarchived conversation update events."""
        return self._create_decorator(
            "teamUnarchived", auth_handlers=auth_handlers, rank=rank
        )
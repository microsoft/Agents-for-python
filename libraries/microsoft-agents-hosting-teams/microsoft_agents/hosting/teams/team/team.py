# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams team conversation update events."""

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
from microsoft_agents.hosting.teams._utils import (
    _get_channel_data,
    _get_channel_event_type,
)

from .route_handlers import TeamUpdateHandler


class Team(Generic[StateT]):
    """Route registration for Teams team conversation update events.

    Access via :attr:`TeamsAgentExtension.teams` (property currently missing — see known issues).
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def _create_decorator(
        self,
        event_type: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Build a route decorator for a specific Teams team event type.

        :param event_type: The ``eventType`` value to match (e.g. ``"teamArchived"``).
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority rank.
        :return: A decorator that registers the handler.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: TeamUpdateHandler[StateT]) -> TeamUpdateHandler[StateT]:

            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                team_data = _get_channel_data(context)
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
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamUnarchived conversation update events."""
        return self._create_decorator(
            "teamUnarchived", auth_handlers=auth_handlers, rank=rank
        )

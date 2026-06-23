# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams team conversation update events."""

import re
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
from microsoft_agents.hosting.msteams._utils import (
    _get_channel_data,
    _get_channel_event_type,
)

from .route_handlers import TeamUpdateHandler


class Team(Generic[StateT]):
    """Route registration for Teams team conversation update events.

    Access via :attr:`TeamsAgentExtension.teams`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def _create_decorator(
        self,
        event_type: str | re.Pattern,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Build a route decorator for a specific Teams team event type."""

        def __selector(context: TurnContext) -> bool:

            event_match = False
            channel_event_type = _get_channel_event_type(context)
            if channel_event_type:
                if isinstance(event_type, re.Pattern):
                    event_match = (
                        re.fullmatch(event_type, channel_event_type) is not None
                    )
                else:
                    event_match = event_type == channel_event_type

            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and event_match
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

    @overload
    def event(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def event(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def event(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams team event conversation update events."""
        decorator = self._create_decorator(
            r"team.*", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def archived(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def archived(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def archived(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamArchived conversation update events."""
        decorator = self._create_decorator(
            "teamArchived", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def deleted(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def deleted(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def deleted(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamDeleted conversation update events."""
        decorator = self._create_decorator(
            "teamDeleted", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def hard_deleted(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def hard_deleted(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def hard_deleted(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamHardDeleted conversation update events."""
        decorator = self._create_decorator(
            "teamHardDeleted", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def renamed(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def renamed(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def renamed(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamRenamed conversation update events."""
        decorator = self._create_decorator(
            "teamRenamed", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def restored(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def restored(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def restored(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamRestored conversation update events."""
        decorator = self._create_decorator(
            "teamRestored", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def unarchived(
        self, handler: TeamUpdateHandler[StateT]
    ) -> TeamUpdateHandler[StateT]: ...
    @overload
    def unarchived(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamUpdateHandler[StateT]]: ...
    def unarchived(
        self,
        handler: Optional[TeamUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamUpdateHandler[StateT] | _RouteDecorator[TeamUpdateHandler[StateT]]:
        """Register a handler for Teams teamUnarchived conversation update events."""
        decorator = self._create_decorator(
            "teamUnarchived", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

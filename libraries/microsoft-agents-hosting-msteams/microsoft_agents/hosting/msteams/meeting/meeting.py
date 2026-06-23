# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams meeting lifecycle event activities."""

from typing import Generic, Optional, overload

from microsoft_teams.api.models.meetings import MeetingDetails

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.activity.teams import MeetingParticipantsEventDetails
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

from .route_handlers import (
    MeetingStartHandler,
    MeetingEndHandler,
    MeetingParticipantsEventHandler,
)


class Meeting(Generic[StateT]):
    """
    Route registration for Teams Meeting event activities.
    Access via TeamsAgentExtension.meetings.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    @overload
    def start(
        self, handler: MeetingStartHandler[StateT]
    ) -> MeetingStartHandler[StateT]: ...
    @overload
    def start(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[MeetingStartHandler[StateT]]: ...
    def start(
        self,
        handler: Optional[MeetingStartHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> MeetingStartHandler[StateT] | _RouteDecorator[MeetingStartHandler[StateT]]:
        """Register a handler for meeting start events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingStart"
            )

        def __call(func: MeetingStartHandler[StateT]) -> MeetingStartHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(teams_context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def end(self, handler: MeetingEndHandler[StateT]) -> MeetingEndHandler[StateT]: ...
    @overload
    def end(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[MeetingEndHandler[StateT]]: ...
    def end(
        self,
        handler: Optional[MeetingEndHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> MeetingEndHandler[StateT] | _RouteDecorator[MeetingEndHandler[StateT]]:
        """Register a handler for meeting end events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingEnd"
            )

        def __call(func: MeetingEndHandler[StateT]) -> MeetingEndHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(teams_context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def participants_join(
        self, handler: MeetingParticipantsEventHandler[StateT]
    ) -> MeetingParticipantsEventHandler[StateT]: ...
    @overload
    def participants_join(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[MeetingParticipantsEventHandler[StateT]]: ...
    def participants_join(
        self,
        handler: Optional[MeetingParticipantsEventHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> (
        MeetingParticipantsEventHandler[StateT]
        | _RouteDecorator[MeetingParticipantsEventHandler[StateT]]
    ):
        """Register a handler for meeting participant join events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantJoin"
            )

        def __call(
            func: MeetingParticipantsEventHandler[StateT],
        ) -> MeetingParticipantsEventHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(teams_context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def participants_leave(
        self, handler: MeetingParticipantsEventHandler[StateT]
    ) -> MeetingParticipantsEventHandler[StateT]: ...
    @overload
    def participants_leave(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[MeetingParticipantsEventHandler[StateT]]: ...
    def participants_leave(
        self,
        handler: Optional[MeetingParticipantsEventHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> (
        MeetingParticipantsEventHandler[StateT]
        | _RouteDecorator[MeetingParticipantsEventHandler[StateT]]
    ):
        """Register a handler for meeting participant leave events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantLeave"
            )

        def __call(
            func: MeetingParticipantsEventHandler[StateT],
        ) -> MeetingParticipantsEventHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(teams_context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

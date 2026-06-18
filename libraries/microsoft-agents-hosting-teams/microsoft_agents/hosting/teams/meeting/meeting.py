# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams meeting lifecycle event activities."""

from typing import Callable, Generic, Optional

from microsoft_teams.api.models import (
    MeetingDetails,
    MeetingParticipant,
)

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)
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
    Access via TeamsAgentExtension.meeting.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def start(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MeetingStartHandler[StateT]]:
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

        return __call

    def end(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MeetingEndHandler[StateT]]:
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

        return __call

    def participants_join(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MeetingParticipantsEventHandler[StateT]]:
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
                details = MeetingParticipant.model_validate(
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

        return __call

    def participants_leave(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MeetingParticipantsEventHandler[StateT]]:
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
                details = MeetingParticipant.model_validate(
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

        return __call

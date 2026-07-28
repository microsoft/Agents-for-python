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

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    _RouteDecorator,
    StateT,
)

from .route_handlers import (
    MeetingStartHandler,
    MeetingEndHandler,
    MeetingParticipantsEventHandler,
)


class Meeting(Generic[StateT]):
    """Route registration for Teams meeting lifecycle event activities.

    Access via :attr:`TeamsAgentExtension.meetings`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
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
        """Register a handler for Teams meeting start events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a Teams meeting start event."""
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingStart"
            )

        def __call(func: MeetingStartHandler[StateT]) -> MeetingStartHandler[StateT]:
            """Register the supplied meeting start handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the core turn context and dispatch to the meeting start handler."""
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
        """Register a handler for Teams meeting end events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a Teams meeting end event."""
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingEnd"
            )

        def __call(func: MeetingEndHandler[StateT]) -> MeetingEndHandler[StateT]:
            """Register the supplied meeting end handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the core turn context and dispatch to the meeting end handler."""
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
        """Register a handler for Teams meeting participant join events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a Teams participant join event."""
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantJoin"
            )

        def __call(
            func: MeetingParticipantsEventHandler[StateT],
        ) -> MeetingParticipantsEventHandler[StateT]:
            """Register the supplied meeting participants handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the core turn context and dispatch to the participants handler."""
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
        """Register a handler for Teams meeting participant leave events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a Teams participant leave event."""
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantLeave"
            )

        def __call(
            func: MeetingParticipantsEventHandler[StateT],
        ) -> MeetingParticipantsEventHandler[StateT]:
            """Register the supplied meeting participants handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the core turn context and dispatch to the participants handler."""
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

class Meeting(Generic[StateT]):
    """
    Route registration for Teams Meeting event activities.
    Access via TeamsAgentExtension.meeting.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def on_start(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting start events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingStart"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_end(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting end events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingEnd"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_participants_join(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting participant join events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantJoin"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_participants_leave(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting participant leave events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantLeave"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

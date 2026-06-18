# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams channel conversation update events."""

from typing import Generic, Optional, overload

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

from .route_handlers import ChannelUpdateHandler


class Channel(Generic[StateT]):
    """Route registration for Teams channel conversation update events.

    Access via :attr:`TeamsAgentExtension.channels`.
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
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Build a route decorator that matches a specific Teams channel event type."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: ChannelUpdateHandler[StateT]) -> ChannelUpdateHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func

        return __call

    @overload
    def created(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def created(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def created(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelCreated conversation update events."""
        decorator = self._create_decorator(
            "channelCreated", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def deleted(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def deleted(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def deleted(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelDeleted conversation update events."""
        decorator = self._create_decorator(
            "channelDeleted", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def renamed(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def renamed(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def renamed(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelRenamed conversation update events."""
        decorator = self._create_decorator(
            "channelRenamed", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def rest(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def rest(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def rest(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelRestored conversation update events."""
        decorator = self._create_decorator(
            "channelRestored", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def members_added(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def members_added(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def members_added(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams membersAdded conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_added, list)
                and len(context.activity.members_added) > 0
            )

        def __call(func: ChannelUpdateHandler[StateT]) -> ChannelUpdateHandler[StateT]:
            async def __func(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def members_removed(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def members_removed(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def members_removed(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams membersRemoved conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_removed, list)
                and len(context.activity.members_removed) > 0
            )

        def __call(func: ChannelUpdateHandler[StateT]) -> ChannelUpdateHandler[StateT]:
            async def __func(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

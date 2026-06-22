# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams channel conversation update events."""

import re
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
        event_type: str | re.Pattern,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Build a route decorator that matches a specific Teams channel event type."""

        def __selector(context: TurnContext) -> bool:
            event_match = False
            channel_event_type = _get_channel_event_type(context)
            if channel_event_type:
                if isinstance(event_type, re.Pattern):
                    event_match = re.fullmatch(event_type, channel_event_type) is not None
                else:
                    event_match = event_type == channel_event_type

            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and event_match
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
    def event(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def event(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def event(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams team event conversation update events."""
        decorator = self._create_decorator(
            r"channel.*", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

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
    def shared(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def shared(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def shared(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelShared conversation update events."""
        decorator = self._create_decorator(
            "channelShared", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator
    
    @overload
    def unshared(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def unshared(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def unshared(
        self,
        handler: Optional[ChannelUpdateHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ChannelUpdateHandler[StateT] | _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelUnshared conversation update events."""
        decorator = self._create_decorator(
            "channelUnshared", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def restored(
        self, handler: ChannelUpdateHandler[StateT]
    ) -> ChannelUpdateHandler[StateT]: ...
    @overload
    def restored(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]: ...
    def restored(
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

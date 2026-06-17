# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Generic, Optional

from microsoft_teams.api.models.channel_data import ChannelData

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
    _send_invoke_response,
    _get_channel_event_type,
)

from .route_handlers import ChannelUpdateHandler

def _get_channel_data(context: TurnContext) -> ChannelData:
    data = context.activity.channel_data
    if data is None:
        return ChannelData()
    if isinstance(data, dict):
        return ChannelData(**data)
    return ChannelData.model_validate(data)

class Channel(Generic[StateT]):

    def __init__(self, app: AgentApplication[StateT]):
        self._app = app

    def _create_decorator(
        self,
        event_type: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: ChannelUpdateHandler[StateT]) -> ChannelUpdateHandler[StateT]:

            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func

        return __call


    def created(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelCreated conversation update events."""
        return self._create_decorator(
            "channelCreated", auth_handlers=auth_handlers, rank=rank
        )

    def deleted(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelDeleted conversation update events."""
        return self._create_decorator(
            "channelDeleted", auth_handlers=auth_handlers, rank=rank
        )

    def renamed(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelRenamed conversation update events."""
        return self._create_decorator(
            "channelRenamed", auth_handlers=auth_handlers, rank=rank
        )

    def rest(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
        """Register a handler for Teams channelRestored conversation update events."""
        return self._create_decorator(
            "channelRestored", auth_handlers=auth_handlers, rank=rank
        )
    
    def on_members_added(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
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
                teams_context = TeamsTurnContext(context)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __func, rank=rank, auth_handlers=auth_handlers
            )

            return func

        return __call

    def on_members_removed(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ChannelUpdateHandler[StateT]]:
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
                teams_context = TeamsTurnContext(context)
                channel_data = _get_channel_data(context)
                await func(teams_context, state, channel_data)

            self._app.add_route(
                __selector, __func, rank=rank, auth_handlers=auth_handlers
            )

            return func

        return __call
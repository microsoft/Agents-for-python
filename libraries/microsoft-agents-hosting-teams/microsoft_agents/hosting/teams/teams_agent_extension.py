"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any, Callable, Generic, Optional, Pattern, TypeVar

from microsoft_agents.activity import Activity, ActivityTypes, InvokeResponse
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.core.app.state import TurnState

from microsoft_agents.activity.teams import (
    MeetingParticipantsEventDetails,
    ReadReceiptInfo,
)
from microsoft_teams.api.models import (
    AppBasedLinkQuery,
    FileConsentCardResponse,
    MeetingDetails,
    MessagingExtensionAction,
    MessagingExtensionQuery,
    O365ConnectorCardActionQuery,
    TaskModuleRequest,
)

from .channel import Channel
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .task_module import TaskModule
from .team import Team

from .type_defs import (
    StateT
)


class TeamsAgentExtension(Generic[StateT]):
    """
    Adds Teams-specific route registration to an AgentApplication.

    Usage::

        app = AgentApplication(options)
        teams = TeamsAgentExtension(app)

        @teams.task_module.on_fetch("myVerb")
        async def handle_fetch(context, state, request: TaskModuleRequest):
            return TaskModuleResponse(...)

        @teams.message_extension.on_query("searchCmd")
        async def handle_query(context, state, query: MessagingExtensionQuery):
            return MessagingExtensionResponse(...)

        @teams.meeting.on_start
        async def handle_meeting_start(context, state, meeting: MeetingDetails):
            ...
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app
        self._message_extension: MessageExtension[StateT] = MessageExtension(app)
        self._task_module: TaskModule[StateT] = TaskModule(app)
        self._meeting: Meeting[StateT] = Meeting(app)
        self._message: Message[StateT] = Message(app)
        self._team: Team[StateT] = Team(app)
        self._channel: Channel[StateT] = Channel(app)

    @property
    def message_extension(self) -> MessageExtension[StateT]:
        """Route registration for Message Extension (composeExtension) invokes."""
        return self._message_extension

    @property
    def task_module(self) -> TaskModule[StateT]:
        """Route registration for Task Module (task/fetch, task/submit) invokes."""
        return self._task_module

    @property
    def meeting(self) -> Meeting[StateT]:
        """Route registration for Meeting lifecycle events."""
        return self._meeting
    
    @property
    def message(self) -> Message[StateT]:
        """Route registration for messaging activities."""
        return self._message

    # ── Message update / delete ────────────────────────────────────────────

    def on_message_edit(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams editMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "editMessage"
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_message_undelete(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams undeleteMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "undeleteMessage"
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_message_soft_delete(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams softDeleteMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_delete
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "softDeleteMessage"
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    # ── Read receipt ───────────────────────────────────────────────────────

    def on_read_receipt(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams readReceipt events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.readReceipt"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                receipt = ReadReceiptInfo.model_validate(context.activity.value or {})
                await func(context, state, receipt)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    # ── Config ─────────────────────────────────────────────────────────────

    def on_config_fetch(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for config/fetch invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "config/fetch"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                response = await func(context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_config_submit(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for config/submit invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "config/submit"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                response = await func(context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    # ── File consent ───────────────────────────────────────────────────────

    def on_file_consent_accept(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for fileConsent/invoke with action == 'accept'."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "fileConsent/invoke"
                and isinstance(context.activity.value, dict)
                and context.activity.value.get("action") == "accept"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                file_consent = FileConsentCardResponse.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, file_consent)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_file_consent_decline(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for fileConsent/invoke with action == 'decline'."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "fileConsent/invoke"
                and isinstance(context.activity.value, dict)
                and context.activity.value.get("action") == "decline"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                file_consent = FileConsentCardResponse.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, file_consent)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    # ── O365 Connector ─────────────────────────────────────────────────────

    def on_o365_connector_card_action(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for actionableMessage/executeAction invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "actionableMessage/executeAction"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = O365ConnectorCardActionQuery.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, query)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    # ── Conversation update events ─────────────────────────────────────────

    def on_members_added(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams membersAdded conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_added, list)
                and len(context.activity.members_added) > 0
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_members_removed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams membersRemoved conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_removed, list)
                and len(context.activity.members_removed) > 0
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def on_channel_created(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelCreated conversation update events."""
        return self._on_teams_channel_event(
            "channelCreated", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelDeleted conversation update events."""
        return self._on_teams_channel_event(
            "channelDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_renamed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelRenamed conversation update events."""
        return self._on_teams_channel_event(
            "channelRenamed", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_restored(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelRestored conversation update events."""
        return self._on_teams_channel_event(
            "channelRestored", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_archived(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamArchived conversation update events."""
        return self._on_teams_channel_event(
            "teamArchived", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamDeleted conversation update events."""
        return self._on_teams_channel_event(
            "teamDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_hard_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamHardDeleted conversation update events."""
        return self._on_teams_channel_event(
            "teamHardDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_renamed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamRenamed conversation update events."""
        return self._on_teams_channel_event(
            "teamRenamed", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_restored(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamRestored conversation update events."""
        return self._on_teams_channel_event(
            "teamRestored", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_unarchived(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamUnarchived conversation update events."""
        return self._on_teams_channel_event(
            "teamUnarchived", handler, auth_handlers=auth_handlers, rank=rank
        )

    def _on_teams_channel_event(
        self,
        event_type: str,
        handler: Optional[Callable],
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

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
from .configuration import Configuration
from .file_consent import FileConsent
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


        self._channel: Channel[StateT] = Channel(app)
        self._configuration: Configuration[StateT] = Configuration(app)
        self._file_consent: FileConsent[StateT] = FileConsent(app)
        self._meeting: Meeting[StateT] = Meeting(app)
        self._message: Message[StateT] = Message(app)
        self._message_extension: MessageExtension[StateT] = MessageExtension(app)
        self._task_module: TaskModule[StateT] = TaskModule(app)
        self._team: Team[StateT] = Team(app)
    
    @property
    def channel(self) -> Channel[StateT]:
        """Route registration for Channel events."""
        return self._channel

    @property
    def configuration(self) -> Configuration[StateT]:
        """Route registration for Configuration events."""
        return self._configuration
    
    @property
    def file_consent(self) -> FileConsent[StateT]:
        """Route registration for File Consent events."""
        return self._file_consent

    @property
    def meeting(self) -> Meeting[StateT]:
        """Route registration for Meeting lifecycle events."""
        return self._meeting

    @property
    def message(self) -> Message[StateT]:
        """Route registration for messaging activities."""
        return self._message

    @property
    def message_extension(self) -> MessageExtension[StateT]:
        """Route registration for Message Extension (composeExtension) invokes."""
        return self._message_extension

    @property
    def task_module(self) -> TaskModule[StateT]:
        """Route registration for Task Module (task/fetch, task/submit) invokes."""
        return self._task_module
    

    
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
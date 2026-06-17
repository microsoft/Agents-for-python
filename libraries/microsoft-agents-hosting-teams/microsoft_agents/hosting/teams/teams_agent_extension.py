"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Generic

from microsoft_agents.hosting.core.app import AgentApplication

from .channel import Channel
from .configuration import Configuration
from .file_consent import FileConsent
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .task_module import TaskModule
from .team import Team

from .type_defs import StateT


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
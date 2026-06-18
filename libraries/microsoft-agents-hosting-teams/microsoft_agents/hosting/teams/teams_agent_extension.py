"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import (
    Awaitable,
    Callable,
    Generic,
    Optional,
    Pattern,
    Protocol,
)

from microsoft_agents.activity import (
    ActivityTypes,
    ConversationUpdateTypes,
    MessageReactionTypes,
    MessageUpdateTypes,
)
from microsoft_agents.hosting.core import AgentApplication
from microsoft_agents.hosting.core.app._type_defs import (
    RouteHandler,
    HandoffHandler
)

from .channel import Channel
from .configuration import Configuration
from .file_consent import FileConsent
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .route_handlers import TeamsRouteHandler, TeamsHandoffHandler
from .task_module import TaskModule
from .team import Team

from .type_defs import StateT, _RouteDecorator

class _AppRouteDecorator(Protocol[StateT]):
    def __call__(self, func: TeamsRouteHandler[StateT], /) -> RouteHandler[StateT]: ...

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
    def channels(self) -> Channel[StateT]:
        """Route registration for Channel events."""
        return self._channel

    @property
    def config(self) -> Configuration[StateT]:
        """Route registration for Configuration events."""
        return self._configuration
    
    @property
    def file_consent(self) -> FileConsent[StateT]:
        """Route registration for File Consent events."""
        return self._file_consent

    @property
    def meetings(self) -> Meeting[StateT]:
        """Route registration for Meeting lifecycle events."""
        return self._meeting

    @property
    def messages(self) -> Message[StateT]:
        """Route registration for messaging activities."""
        return self._message

    @property
    def message_extensions(self) -> MessageExtension[StateT]:
        """Route registration for Message Extension (composeExtension) invokes."""
        return self._message_extension

    @property
    def task_modules(self) -> TaskModule[StateT]:
        """Route registration for Task Module (task/fetch, task/submit) invokes."""
        return self._task_module
    
    # AgentApplication route hooks

    def _wrap_decorator(
        self,
        decorator: _RouteDecorator[RouteHandler[StateT]]
    ) -> Callable[[TeamsRouteHandler[StateT]], RouteHandler[StateT]]:
        """Wrap a core route decorator to create a Teams-specific route decorator."""
        def __call(func: TeamsRouteHandler[StateT]) -> RouteHandler[StateT]:
            return decorator(TeamsRouteHandler.wrap(func))
        return __call

    def activity(
        self,
        activity_type: str | ActivityTypes | list[str | ActivityTypes],
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        return self._wrap_decorator(
            self._app.activity(activity_type, auth_handlers=auth_handlers, **kwargs)
        )
    
    def message(
        self,
        select: str | Pattern[str] | list[str | Pattern[str]],
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        return self._wrap_decorator(
            self._app.message(select, auth_handlers=auth_handlers, **kwargs)
        )
    
    def conversation_update(
        self,
        type: ConversationUpdateTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        return self._wrap_decorator(
            self._app.conversation_update(type, auth_handlers=auth_handlers, **kwargs)
        )
    
    def message_reaction(
        self,
        type: MessageReactionTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        return self._wrap_decorator(
            self._app.message_reaction(type, auth_handlers=auth_handlers, **kwargs)
        )
    
    def message_update(
        self,
        type: MessageUpdateTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        return self._wrap_decorator(
            self._app.message_update(type, auth_handlers=auth_handlers, **kwargs)
        )
    
    def handoff(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[TeamsHandoffHandler[StateT]], HandoffHandler[StateT]]:
        def __call(func: TeamsHandoffHandler[StateT]) -> HandoffHandler[StateT]:
            return self._app.handoff(auth_handlers=auth_handlers, **kwargs)(
                TeamsHandoffHandler.wrap(func)
            )
        return __call
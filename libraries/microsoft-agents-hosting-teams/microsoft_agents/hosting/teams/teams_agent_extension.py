"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Teams-specific extension for :class:`AgentApplication` that exposes route
registration helpers for every Teams invoke / event surface.
"""

from __future__ import annotations

from typing import (
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
from microsoft_agents.hosting.core.app._type_defs import RouteHandler, HandoffHandler

from .channel import Channel
from .config import Config
from .file_consent import FileConsent
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .route_handlers import TeamsRouteHandler, TeamsHandoffHandler
from .task_module import TaskModule
from .team import Team

from .type_defs import StateT, _RouteDecorator


class _AppRouteDecorator(Protocol[StateT]):
    """Protocol for a decorator returned by :class:`TeamsAgentExtension` route methods."""

    def __call__(self, func: TeamsRouteHandler[StateT], /) -> RouteHandler[StateT]:
        """Register *func* as a Teams route handler.

        :param func: Teams-aware handler to register.
        :return: The wrapped core route handler.
        """
        ...


class TeamsAgentExtension(Generic[StateT]):
    """
    Adds Teams-specific route registration to an AgentApplication.

    Usage::

        app = AgentApplication(options)
        teams = TeamsAgentExtension(app)

        @teams.task_modules.fetch("myVerb")
        async def handle_fetch(context, state, request: TaskModuleRequest):
            return TaskModuleResponse(...)

        @teams.message_extensions.query("searchCmd")
        async def handle_query(context, state, query: MessagingExtensionQuery):
            return MessagingExtensionResponse(...)

        @teams.meetings.start()
        async def handle_meeting_start(context, state, meeting: MeetingDetails):
            ...
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Attach Teams route namespaces to *app*.

        :param app: The :class:`AgentApplication` to extend with Teams-specific routes.
        """
        self._app = app

        self._channel: Channel[StateT] = Channel(app)
        self._configuration: Config[StateT] = Config(app)
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
    def config(self) -> Config[StateT]:
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

    @property
    def teams(self) -> Team[StateT]:
        """Route registration for Team lifecycle events."""
        return self._team

    # AgentApplication route hooks

    def _wrap_decorator(
        self, decorator: _RouteDecorator[RouteHandler[StateT]]
    ) -> Callable[[TeamsRouteHandler[StateT]], RouteHandler[StateT]]:
        """Wrap a core route decorator so it accepts a :class:`TeamsRouteHandler`.

        The returned decorator converts the Teams handler via
        :meth:`TeamsRouteHandler.wrap` before passing it to *decorator*, keeping the
        Teams context upgrade transparent to callers.

        :param decorator: A core route decorator from :class:`AgentApplication`.
        :return: A decorator that accepts and registers a :class:`TeamsRouteHandler`.
        """

        def __call(func: TeamsRouteHandler[StateT]) -> RouteHandler[StateT]:
            return decorator(TeamsRouteHandler.wrap(func, self._app))

        return __call

    def activity(
        self,
        activity_type: str | ActivityTypes | list[str | ActivityTypes],
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        """Register a handler for one or more activity types.

        :param activity_type: Activity type(s) to match (e.g. ``ActivityTypes.message``).
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
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
        """Register a handler for message activities matching *select*.

        :param select: A literal string, regex pattern, or list of either to match against
            the message text.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
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
        """Register a handler for a specific conversation update event type.

        :param type: The :class:`ConversationUpdateTypes` value to match.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
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
        """Register a handler for a specific message reaction type.

        :param type: The :class:`MessageReactionTypes` value to match (e.g. ``reactionsAdded``).
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
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
        """Register a handler for a specific message update event type.

        :param type: The :class:`MessageUpdateTypes` value to match (e.g. ``editMessage``).
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.message_update(type, auth_handlers=auth_handlers, **kwargs)
        )

    def handoff(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[TeamsHandoffHandler[StateT]], HandoffHandler[StateT]]:
        """Register a Teams handoff handler.

        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """

        def __call(func: TeamsHandoffHandler[StateT]) -> HandoffHandler[StateT]:
            return self._app.handoff(auth_handlers=auth_handlers, **kwargs)(
                TeamsHandoffHandler.wrap(func, self._app)
            )

        return __call

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""The :class:`TeamsAgentExtension` entry point for Teams route registration.

Attaches Teams-specific route namespaces (channels, teams, meetings, messages,
message extensions, task modules, configuration, and file consent) to an
:class:`AgentApplication`, wires the Teams before-turn hook, and exposes helpers
for obtaining Teams API and Microsoft Graph clients.
"""

from __future__ import annotations

from typing import (
    Callable,
    Generic,
    Optional,
    Pattern,
    Protocol,
)

from msgraph import GraphServiceClient
from microsoft_teams.api import ApiClient

from microsoft_agents.activity import (
    ActivityTypes,
    Channels,
    ConversationUpdateTypes,
    MessageReactionTypes,
    MessageUpdateTypes,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
)
from microsoft_agents.hosting.core.app._type_defs import RouteHandler, HandoffHandler

from .channel import Channel
from .config import Config
from .file_consent import FileConsent
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .route_handlers import (
    TeamsRouteHandler,
    TeamsHandoffHandler,
    wrap_teams_route_handler,
    wrap_teams_handoff_handler,
)
from .task_module import TaskModule
from .team import Team

from ._graph import (
    _DEFAULT_GRAPH_BASE_URL,
    _create_user_graph_service_client,
    _common_get_app_graph_client,
    _common_get_app_graph_client_for_connection,
)

from ._teams_api_client import (
    _get_teams_api_client,
    _set_teams_api_client,
)
from ._utils import _try_get_channel_data

from .teams_activity import TeamsActivity
from .type_defs import StateT


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

        self._configure_app()

    def _configure_app(self):
        """Configure the underlying AgentApplication with Teams-specific routes."""

        async def on_before_turn(context: TurnContext, state: StateT) -> bool:
            if context.activity.channel_id == Channels.ms_teams:
                _set_teams_api_client(context, self._app.connection_manager)
                # caches the deserialized version of ChannelData
                context.activity.channel_data = _try_get_channel_data(context.activity)
            return True

        self._app.before_turn(on_before_turn)

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
        self, decorator: Callable[[RouteHandler[StateT]], RouteHandler[StateT]]
    ) -> Callable[[TeamsRouteHandler[StateT]], RouteHandler[StateT]]:
        """Wrap a core route decorator so it accepts a :class:`TeamsRouteHandler`.

        The returned decorator converts the Teams handler via
        :func:`wrap_teams_route_handler` before passing it to *decorator*, keeping the
        Teams context upgrade transparent to callers.

        :param decorator: A core route decorator from :class:`AgentApplication`.
        :return: A decorator that accepts and registers a :class:`TeamsRouteHandler`.
        """

        def __call(func: TeamsRouteHandler[StateT]) -> RouteHandler[StateT]:
            return decorator(wrap_teams_route_handler(func, self._app))

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
                wrap_teams_handoff_handler(func, self._app)
            )

        return __call

    def get_teams_api_client(self, context: TurnContext) -> ApiClient:
        """Get the Teams API client.

        :return: The Teams API client.
        """
        return _get_teams_api_client(context)

    def get_graph_client(
        self, context: TurnContext, handler_name: str | None = None
    ) -> GraphServiceClient:
        """Get the Graph Service client.

        :param context: The turn context.
        :param handler_name: The name of the handler.
        :return: The Graph Service client.
        """
        return _create_user_graph_service_client(self._app, context, handler_name)

    def get_app_graph_client(
        self, context: TurnContext, graph_base_url: str = _DEFAULT_GRAPH_BASE_URL
    ) -> GraphServiceClient:
        """Get the Graph Service client for the agent application.

        :param context: The turn context.
        :param connection_name: The name of the connection to use for authentication.
        :param graph_base_url: The base URL for the Microsoft Graph API.
        :return: The Graph Service client.
        """
        return _common_get_app_graph_client(
            self._app, context, graph_base_url=graph_base_url
        )

    def get_app_graph_client_for_connection(
        self, connection_name: str, graph_base_url: str = _DEFAULT_GRAPH_BASE_URL
    ) -> GraphServiceClient:
        """Get the Graph Service client for the agent application using a specific connection.

        :param context: The turn context.
        :param connection_name: The name of the connection to use for authentication.
        :param graph_base_url: The base URL for the Microsoft Graph API.
        :return: The Graph Service client.
        """
        return _common_get_app_graph_client_for_connection(
            self._app, connection_name=connection_name, graph_base_url=graph_base_url
        )

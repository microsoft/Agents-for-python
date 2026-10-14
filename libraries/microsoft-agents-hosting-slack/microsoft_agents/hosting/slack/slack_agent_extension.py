"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import warnings

from typing import Any, Callable, Generic, TypeVar
from typing_extensions import deprecated

from microsoft_agents.activity import (
    Channels,
    ConversationUpdateTypes,
)
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication
from microsoft_agents.hosting.core.app._type_defs import (
    RouteHandler,
    _RouteDecorator,
    TextSelector,
)
from microsoft_agents.hosting.core.app.state import TurnState

from .api import (
    SlackApi,
    SlackChannelData,
    SlackResponse,
    SlackStream,
)
from .route_handlers import SlackRouteHandler, wrap_slack_route_handler

StateT = TypeVar("StateT", bound=TurnState)


def _is_slack_channel(context: TurnContext) -> bool:
    return context.activity.channel_id == Channels.slack.value


class SlackAgentExtension(Generic[StateT]):
    """
    Slack-specific route registration and helpers for an
    :class:`~microsoft_agents.hosting.core.app.AgentApplication`.

    Handlers registered with :meth:`message`, :meth:`event`,
    :meth:`conversation_update`, :meth:`members_added`,
    :meth:`members_removed`, or :meth:`installation_update` match only Slack
    activities and receive a :class:`SlackTurnContext` with a typed
    :class:`SlackActivity`.
    Pass ``slack_api=...`` to configure the extension's default API client.
    Before each Slack turn, this client is registered in turn services only
    if no :class:`SlackApi` is already present. Clients supplied by middleware
    or an earlier ``before_turn`` handler are preserved, so ``context.client``,
    :meth:`call`, and :meth:`create_stream` use the same per-turn instance.

    Usage::

        from microsoft_agents.hosting.slack import SlackAgentExtension, SlackTurnContext

        app = AgentApplication(options)
        slack = SlackAgentExtension(app)

        @slack.message("hello")
        async def greet(context: SlackTurnContext, state):
            channel_data = context.activity.slack_channel_data
            await slack.call(
                context,
                "chat.postMessage",
                {
                    "channel": channel_data.channel,
                    "text": f"Hi, {context.activity.from_property.name}!",
                },
                token=channel_data.api_token or "",
            )
    """

    def __init__(
        self,
        application: AgentApplication[StateT],
        *,
        slack_api: SlackApi | None = None,
    ) -> None:
        """Initialise the Slack agent extension with the given application and optional Slack API client.

        :param application: The agent application that this extension is attached to.
        :param slack_api: Optional default SlackApi client to use for turns where no per-turn client is supplied.
        """
        self._app = application
        self._slack_api = slack_api

        async def __on_before_turn(context: TurnContext, state: StateT) -> bool:

            if _is_slack_channel(context) and not context.services.has(SlackApi):
                # Bind the default only when no per-turn client was supplied,
                # so SlackTurnContext.client and any
                # out-of-band SlackAgentExtension.call()/create_stream() calls
                # made during this turn resolve to the same client instance.
                #
                # Note: unlike the C# extension, this does not reset the
                # agent's typing-indicator timer on out-of-band calls, since
                # core AgentApplication does not currently expose an
                # equivalent public API.
                context.services.set(SlackApi, self.slack_api)
            return True

        application.before_turn(__on_before_turn)

    @property
    def slack_api(self) -> SlackApi:
        """Gets the shared SlackApi instance. Creates a new one if it doesn't exist."""
        if not self._slack_api:
            self._slack_api = SlackApi()
        return self._slack_api

    def _get_slack_api(self, turn_context: TurnContext) -> SlackApi:
        """Retrieve the SlackApi instance for the current turn context, falling back to the default client if none is set."""
        if turn_context is not None and turn_context.services.has(SlackApi):
            return turn_context.services.get(SlackApi) or self.slack_api
        return self.slack_api

    # ── direct Slack API access ────────────────────────────────────────────

    async def call(
        self,
        turn_context: TurnContext,
        method: str,
        options: Any = None,
        token: str = "",
    ) -> SlackResponse:
        """Invoke a Slack Web API method, preferring a per-turn :class:`SlackApi`
        if one has been cached on ``turn_context.services``.

        :param turn_context: The current turn context.
        :param method: The Slack Web API method to call.
        :param options: Optional parameters for the API call.
        :param token: Optional Slack API token to use for the call.
        :return: The response from the Slack API.
        """
        api = self._get_slack_api(turn_context)
        return await api.call(method, options, token)

    async def create_stream(
        self,
        turn_context: TurnContext,
        thread_ts: str | None = None,
    ) -> SlackStream:
        """Create and start a :class:`SlackStream` for the current Slack thread.

        Requires a Slack event envelope with a non-empty string
        ``event.channel`` and either an explicit non-empty string ``thread_ts``
        or an ``event.ts`` timestamp. Uses the per-turn :class:`SlackApi` when
        registered, otherwise the extension's default client.

        :return: A started stream ready to append content and stop.
        :raises ValueError: If the envelope, channel, or timestamp is missing
            or invalid, before making an API call.
        """
        channel_data = SlackChannelData.from_activity(turn_context.activity)
        if channel_data.envelope is None:
            raise ValueError(
                "create_stream requires a Slack event envelope on the activity"
            )
        channel = channel_data.envelope.get("event.channel")
        if not isinstance(channel, str) or not channel:
            raise ValueError("create_stream requires a non-empty event.channel")
        resolved_thread_ts = thread_ts or channel_data.envelope.get("event.ts")
        if not isinstance(resolved_thread_ts, str) or not resolved_thread_ts:
            raise ValueError("create_stream requires a non-empty thread_ts or event.ts")
        api = self._get_slack_api(turn_context)
        stream = SlackStream(
            api,
            channel,
            resolved_thread_ts,
            channel_data.api_token or "",
        )
        return await stream.start()

    # ── message routes ─────────────────────────────────────────────────────

    def message(
        self,
        select: TextSelector | None = None,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for Slack message activities.

        :param select: Optional text selector to match the incoming message text.
        :type select: TextSelector | None
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: list[str] | None
        :param kwargs: Additional route configuration passed to :meth:`microsoft_agents.hosting.core.AgentApplication.add_route`.
        """
        return self._wrap_decorator(
            self._app.message(
                select, auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

    @deprecated(
        "SlackAgentExtension.on_message is deprecated; use SlackAgentExtension.message instead."
    )
    def on_message(
        self,
        select: TextSelector | None = None,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Deprecated alias for :meth:`message`; emits ``DeprecationWarning``."""
        return self.message(select, auth_handlers=auth_handlers, **kwargs)

    # ── event routes ───────────────────────────────────────────────────────

    def event(
        self,
        select: TextSelector | None = None,
        *,
        event_name: str | None = None,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for Slack event activities.

        :param select: Optional text selector to match the incoming event name.
        :type select: TextSelector | None
        :param event_name: (Deprecated) Optional specific event name to match.
        :type event_name: str | None
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: list[str] | None
        :param kwargs: Additional route configuration passed to :meth:`microsoft_agents.hosting.core.AgentApplication.add_route`.
        """
        if event_name is not None:
            warnings.warn(
                "The `event_name` parameter is deprecated; use `select` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self._wrap_decorator(
            self._app.event(
                select, auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

    @deprecated(
        "SlackAgentExtension.on_event is deprecated; use SlackAgentExtension.event instead."
    )
    def on_event(
        self,
        event_name: TextSelector | None = None,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Deprecated alias for :meth:`event`; emits ``DeprecationWarning``."""
        return self.event(select, auth_handlers=auth_handlers, **kwargs)

    # ── AgentApplication route hooks ───────────────────────────────────────

    def _wrap_decorator(
        self, decorator: Callable[[RouteHandler[StateT]], RouteHandler[StateT]]
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Wrap a core route decorator so it accepts a :class:`SlackRouteHandler`.

        The handler is converted via :func:`wrap_slack_route_handler` before being
        passed to *decorator*, and the original handler is returned.

        :param decorator: A core route decorator from :class:`AgentApplication`.
        :return: A decorator that registers a :class:`SlackRouteHandler`.
        """

        def __call(func: SlackRouteHandler[StateT]) -> SlackRouteHandler[StateT]:
            decorator(wrap_slack_route_handler(func, self._app))
            return func

        return __call

    def conversation_update(
        self,
        type: ConversationUpdateTypes | str,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs: Any,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for a Slack conversation update event type.

        Non-Slack activities never match. The handler receives a
        :class:`SlackTurnContext` and the turn state.

        :param type: The :class:`ConversationUpdateTypes` value to match (e.g. ``membersAdded``).
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param kwargs: Additional route configuration, such as ``rank``, passed to
            :meth:`AgentApplication.add_route`.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.conversation_update(
                type, auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

    def members_added(
        self,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs: Any,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for the Slack ``membersAdded`` event.

        Non-Slack activities never match. The handler receives a
        :class:`SlackTurnContext` and the turn state.

        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param kwargs: Additional route configuration, such as ``rank``, passed to
            :meth:`AgentApplication.add_route`.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.members_added(
                auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

    def members_removed(
        self,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs: Any,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for the Slack ``membersRemoved`` event.

        Non-Slack activities never match. The handler receives a
        :class:`SlackTurnContext` and the turn state.

        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param kwargs: Additional route configuration, such as ``rank``, passed to
            :meth:`AgentApplication.add_route`.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.members_removed(
                auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

    def installation_update(
        self,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs: Any,
    ) -> _RouteDecorator[SlackRouteHandler[StateT]]:
        """Register a handler for the Slack ``installationUpdate`` event.

        Non-Slack activities never match. The handler receives a
        :class:`SlackTurnContext` and the turn state.

        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param kwargs: Additional route configuration, such as ``rank``, passed to
            :meth:`AgentApplication.add_route`.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.installation_update(
                auth_handlers=auth_handlers, channel_id=Channels.slack, **kwargs
            )
        )

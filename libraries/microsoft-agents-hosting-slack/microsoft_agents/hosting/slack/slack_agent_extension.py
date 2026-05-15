"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Generic, Optional, Pattern, TypeVar, Union

from microsoft_agents.activity import ActivityTypes, Channels
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.core.app.state import TurnState

from .api import (
    SlackApi,
    SlackChannelData,
    SlackResponse,
    SlackStream,
)

StateT = TypeVar("StateT", bound=TurnState)

TextSelector = Union[str, Pattern[str], None]

_SLACK_API_SERVICE_KEY = "microsoft_agents.hosting.slack.SlackApi"


def _matches_text(selector: TextSelector, text: Optional[str]) -> bool:
    if selector is None:
        return True
    if text is None:
        return False
    if isinstance(selector, Pattern):
        return re.fullmatch(selector, text) is not None
    return text == selector


def _is_slack_channel(context: TurnContext) -> bool:
    return context.activity.channel_id == Channels.slack.value


class SlackAgentExtension(Generic[StateT]):
    """
    Slack-specific route registration and helpers for an
    :class:`~microsoft_agents.hosting.core.app.AgentApplication`.

    Usage::

        from microsoft_agents.hosting.slack import SlackAgentExtension
        from microsoft_agents.hosting.slack.api import SlackChannelData

        app = AgentApplication(options)
        slack = SlackAgentExtension(app)

        @slack.on_message("hello")
        async def greet(context, state):
            channel_data = SlackChannelData.from_activity(context.activity)
            await slack.call(
                context,
                "chat.postMessage",
                {
                    "channel": channel_data.channel,
                    "text": f"Hi, {context.activity.from_property.name}!",
                },
                token=channel_data.api_token,
            )
    """

    def __init__(
        self,
        application: AgentApplication[StateT],
        *,
        slack_api: Optional[SlackApi] = None,
    ) -> None:
        self._app = application
        self._slack_api = slack_api or SlackApi()

    @property
    def slack_api(self) -> SlackApi:
        """The shared :class:`SlackApi` used by :meth:`call` and :meth:`create_stream`."""
        return self._slack_api

    # ── direct Slack API access ────────────────────────────────────────────

    async def call(
        self,
        turn_context: TurnContext,
        method: str,
        options: Any = None,
        token: str = "",
    ) -> SlackResponse:
        """Invoke a Slack Web API method, preferring a per-turn :class:`SlackApi`
        if one has been cached on ``turn_context.services``."""
        api = self._slack_api
        if turn_context is not None and turn_context.has(_SLACK_API_SERVICE_KEY):
            api = turn_context.get(_SLACK_API_SERVICE_KEY)  # type: ignore[assignment]
        return await api.call(method, options, token)

    async def create_stream(
        self,
        turn_context: TurnContext,
        thread_ts: Optional[str] = None,
    ) -> SlackStream:
        """Create and start a :class:`SlackStream` for the current Slack thread."""
        channel_data = SlackChannelData.from_activity(turn_context.activity)
        if channel_data.envelope is None:
            raise ValueError(
                "create_stream requires a Slack event envelope on the activity"
            )
        resolved_thread_ts = thread_ts or channel_data.envelope.get("event.ts")
        api = self._slack_api
        if turn_context.has(_SLACK_API_SERVICE_KEY):
            api = turn_context.get(_SLACK_API_SERVICE_KEY)  # type: ignore[assignment]
        stream = SlackStream(
            api,
            channel_data.envelope.get("event.channel"),
            resolved_thread_ts,
            channel_data.api_token or "",
        )
        return await stream.start()

    # ── message routes ─────────────────────────────────────────────────────

    def on_message(
        self,
        select: TextSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Slack message activities.

        When ``select`` is ``None``, every Slack message matches; otherwise the
        activity's ``text`` must equal ``select`` (string) or fully match it
        (compiled regex).

        ``rank`` defaults to :attr:`RouteRank.DEFAULT`; when ``select`` is
        ``None`` the rank is downgraded to :attr:`RouteRank.LAST` so explicit
        text routes win — matching the C# behavior.
        """
        effective_rank = (
            RouteRank.LAST if (select is None and rank == RouteRank.DEFAULT) else rank
        )

        def __selector(context: TurnContext) -> bool:
            if context.activity.type != ActivityTypes.message or not _is_slack_channel(
                context
            ):
                return False
            return _matches_text(select, context.activity.text)

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector,
                func,
                rank=effective_rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    # ── event routes ───────────────────────────────────────────────────────

    def on_event(
        self,
        event_name: TextSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Slack event activities.

        When ``event_name`` is ``None``, every Slack event matches; otherwise
        the activity's ``name`` must equal it (string) or fully match it
        (compiled regex).
        """
        effective_rank = (
            RouteRank.LAST
            if (event_name is None and rank == RouteRank.DEFAULT)
            else rank
        )

        def __selector(context: TurnContext) -> bool:
            if context.activity.type != ActivityTypes.event or not _is_slack_channel(
                context
            ):
                return False
            return _matches_text(event_name, context.activity.name)

        def __call(func: Callable) -> Callable:
            self._app.add_route(
                __selector,
                func,
                rank=effective_rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

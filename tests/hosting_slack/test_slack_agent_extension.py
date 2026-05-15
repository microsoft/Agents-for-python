"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.slack import SlackAgentExtension


def _make_app() -> MagicMock:
    app = MagicMock(spec=AgentApplication)
    app.routes = []

    def _add_route(
        selector, handler, is_invoke=False, rank=RouteRank.DEFAULT, auth_handlers=None
    ):
        app.routes.append(
            dict(
                selector=selector,
                handler=handler,
                is_invoke=is_invoke,
                rank=rank,
                auth_handlers=auth_handlers,
            )
        )

    app.add_route.side_effect = _add_route
    return app


def _make_context(
    activity_type: str,
    *,
    channel_id: str = "slack",
    text: str = None,
    name: str = None,
) -> TurnContext:
    activity = MagicMock(spec=Activity)
    activity.type = activity_type
    activity.channel_id = channel_id
    activity.text = text
    activity.name = name
    context = MagicMock(spec=TurnContext)
    context.activity = activity
    context.send_activity = AsyncMock()
    context.has.return_value = False
    return context


class TestOnMessage:
    def setup_method(self):
        self.app = _make_app()
        self.slack = SlackAgentExtension(self.app)

    def test_no_text_matches_any_slack_message(self):
        @self.slack.on_message()
        async def handler(context, state):
            return True

        route = self.app.routes[-1]
        # bare on_message should default to RouteRank.LAST
        assert route["rank"] == RouteRank.LAST
        # matches any Slack message
        assert route["selector"](_make_context(ActivityTypes.message, text="anything"))
        # does NOT match non-slack channels
        assert not route["selector"](
            _make_context(ActivityTypes.message, channel_id="msteams", text="x")
        )
        # does NOT match non-message activities
        assert not route["selector"](_make_context(ActivityTypes.event, text="x"))

    def test_literal_text_match(self):
        @self.slack.on_message("hello")
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.message, text="hello"))
        assert not sel(_make_context(ActivityTypes.message, text="bye"))

    def test_regex_text_match(self):
        @self.slack.on_message(re.compile(r"^-stream\b.*"))
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.message, text="-stream now"))
        assert not sel(_make_context(ActivityTypes.message, text="stream now"))

    def test_custom_rank_preserved(self):
        @self.slack.on_message("hi", rank=RouteRank.FIRST)
        async def handler(context, state):
            return True

        assert self.app.routes[-1]["rank"] == RouteRank.FIRST


class TestOnEvent:
    def setup_method(self):
        self.app = _make_app()
        self.slack = SlackAgentExtension(self.app)

    def test_no_name_matches_any_slack_event(self):
        @self.slack.on_event()
        async def handler(context, state):
            return True

        route = self.app.routes[-1]
        assert route["rank"] == RouteRank.LAST
        assert route["selector"](_make_context(ActivityTypes.event, name="any"))
        assert not route["selector"](
            _make_context(ActivityTypes.event, channel_id="msteams", name="any")
        )
        assert not route["selector"](_make_context(ActivityTypes.message))

    def test_literal_event_name(self):
        @self.slack.on_event("app_mention")
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.event, name="app_mention"))
        assert not sel(_make_context(ActivityTypes.event, name="other"))


class TestCall:
    @pytest.mark.asyncio
    async def test_call_delegates_to_slack_api(self):
        app = _make_app()
        slack_api = MagicMock()
        slack_api.call = AsyncMock(return_value="result")
        slack = SlackAgentExtension(app, slack_api=slack_api)

        ctx = _make_context(ActivityTypes.message)
        out = await slack.call(ctx, "chat.postMessage", {"k": "v"}, token="t")

        assert out == "result"
        slack_api.call.assert_awaited_once_with("chat.postMessage", {"k": "v"}, "t")

    @pytest.mark.asyncio
    async def test_call_prefers_turn_context_service_when_present(self):
        app = _make_app()
        default_api = MagicMock()
        default_api.call = AsyncMock(return_value="default")
        per_turn_api = MagicMock()
        per_turn_api.call = AsyncMock(return_value="per-turn")

        slack = SlackAgentExtension(app, slack_api=default_api)

        ctx = _make_context(ActivityTypes.message)
        ctx.has.return_value = True
        ctx.get.return_value = per_turn_api

        out = await slack.call(ctx, "auth.test")
        assert out == "per-turn"
        per_turn_api.call.assert_awaited_once()
        default_api.call.assert_not_awaited()

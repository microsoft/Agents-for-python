"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ChannelId,
    ConversationAccount,
    DeliveryModes,
)
from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    MemoryStorage,
    TurnContext,
)
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.core.app.state import TurnState
from microsoft_agents.hosting.core.authorization import Connections
from microsoft_agents.hosting.slack import (
    SlackActivity,
    SlackAgentExtension,
    SlackTurnContext,
)
from microsoft_agents.hosting.slack.api import SlackApi, SlackResponse


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
    context.services = MagicMock()
    context.services.has.return_value = False
    return context


class TestMessage:
    def setup_method(self):
        self.app = _make_app()
        self.slack = SlackAgentExtension(self.app)

    def test_no_text_matches_any_slack_message(self):
        @self.slack.message()
        async def handler(context, state):
            return True

        route = self.app.routes[-1]
        # bare message() should default to RouteRank.LAST
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
        @self.slack.message("hello")
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.message, text="hello"))
        assert not sel(_make_context(ActivityTypes.message, text="bye"))

    def test_regex_text_match(self):
        @self.slack.message(re.compile(r"^-stream\b.*"))
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.message, text="-stream now"))
        assert not sel(_make_context(ActivityTypes.message, text="stream now"))

    def test_custom_rank_preserved(self):
        @self.slack.message("hi", rank=RouteRank.FIRST)
        async def handler(context, state):
            return True

        assert self.app.routes[-1]["rank"] == RouteRank.FIRST


class TestEvent:
    def setup_method(self):
        self.app = _make_app()
        self.slack = SlackAgentExtension(self.app)

    def test_no_name_matches_any_slack_event(self):
        @self.slack.event()
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
        @self.slack.event("app_mention")
        async def handler(context, state):
            return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.event, name="app_mention"))
        assert not sel(_make_context(ActivityTypes.event, name="other"))


class TestDeprecatedAliases:
    def setup_method(self):
        self.app = _make_app()
        self.slack = SlackAgentExtension(self.app)

    def test_on_message_is_deprecated_and_delegates_to_message(self):
        with pytest.deprecated_call():

            @self.slack.on_message("hello")
            async def handler(context, state):
                return True

        sel = self.app.routes[-1]["selector"]
        assert sel(_make_context(ActivityTypes.message, text="hello"))
        assert not sel(_make_context(ActivityTypes.message, text="bye"))

    def test_on_event_is_deprecated_and_delegates_to_event(self):
        with pytest.deprecated_call():

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
        ctx.services.has.return_value = True
        ctx.services.get.return_value = per_turn_api

        out = await slack.call(ctx, "auth.test")
        assert out == "per-turn"
        ctx.services.has.assert_called_once_with(SlackApi)
        ctx.services.get.assert_called_once_with(SlackApi)
        per_turn_api.call.assert_awaited_once()
        default_api.call.assert_not_awaited()


class TestTurnPipeline:
    def setup_method(self):
        self.app = AgentApplication(
            storage=MemoryStorage(),
            connection_manager=MagicMock(spec=Connections),
        )
        self.adapter = ChannelServiceAdapter(None)
        self.context = TurnContext(
            self.adapter,
            Activity(
                type=ActivityTypes.message,
                channel_id="slack",
                text="hello",
                name="hello",
                service_url="https://example.invalid",
                conversation=ConversationAccount(id="conversation"),
                from_property=ChannelAccount(id="user"),
                recipient=ChannelAccount(id="bot"),
            ),
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("route_name", ["message", "event"])
    async def test_registered_handler_receives_slack_context(self, route_name):
        app = _make_app()
        slack = SlackAgentExtension(app)
        client = SlackApi()
        self.context.services.set(SlackApi, client)
        self.context.activity.type = route_name
        state = TurnState()

        async def handler(context, received_state):
            assert isinstance(context, SlackTurnContext)
            assert isinstance(context.activity, SlackActivity)
            assert context.activity is self.context.activity
            assert context.services is self.context.services
            assert context.client is client
            assert received_state is state

        delegate = AsyncMock(side_effect=handler)
        register = slack.message if route_name == "message" else slack.event
        assert register("hello")(delegate) is delegate

        await app.routes[-1]["handler"](self.context, state)

        delegate.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "activity_type", [ActivityTypes.message, ActivityTypes.event]
    )
    async def test_wrapped_handlers_preserve_buffered_replies(self, activity_type):
        slack = SlackAgentExtension(self.app)
        self.context.activity.type = activity_type
        self.context.activity.delivery_mode = DeliveryModes.expect_replies
        self.context.buffered_reply_activities.append(
            Activity(type=ActivityTypes.message, text="before")
        )
        register = (
            slack.message if activity_type == ActivityTypes.message else slack.event
        )

        @register("hello")
        async def handler(context, state):
            assert isinstance(context, SlackTurnContext)
            assert isinstance(context.activity, SlackActivity)
            assert context.turn_state is self.context.turn_state
            await context.send_activity("first")
            await context.send_activities(
                [
                    Activity(type=ActivityTypes.message, text="second"),
                    Activity(type=ActivityTypes.message, text="third"),
                ]
            )

        await self.app.on_turn(self.context)

        assert self.context.responded
        response = self.adapter._process_turn_results(self.context)
        assert response.status == 200
        assert [activity["text"] for activity in response.body["activities"]] == [
            "before",
            "first",
            "second",
            "third",
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("client_source", ["default", "services", "before_turn"])
    async def test_client_binding_through_turn_pipeline(self, client_source):
        default_api = MagicMock(spec=SlackApi)
        per_turn_api = MagicMock(spec=SlackApi)
        if client_source == "services":
            self.context.services.set(SlackApi, per_turn_api)
        elif client_source == "before_turn":

            @self.app.before_turn
            async def bind_client(context, state):
                context.services.set(SlackApi, per_turn_api)
                return True

        slack = SlackAgentExtension(self.app, slack_api=default_api)
        expected_api = default_api if client_source == "default" else per_turn_api
        unused_api = per_turn_api if client_source == "default" else default_api
        expected_api.call.return_value = SlackResponse(ok=True, ts="stream-ts")
        self.context.activity.channel_data = {
            "SlackMessage": {"event": {"channel": "C1", "ts": "thread-ts"}},
            "ApiToken": "test-token",
        }

        @slack.message("hello")
        async def handler(context, state):
            assert context.client is expected_api
            await slack.call(context, "auth.test")
            await slack.create_stream(context)

        await self.app.on_turn(self.context)

        assert self.context.services.get(SlackApi) is expected_api
        expected_api.call.assert_has_awaits(
            [
                call("auth.test", None, ""),
                call(
                    "chat.startStream",
                    {
                        "channel": "C1",
                        "thread_ts": "thread-ts",
                        "task_display_mode": "plan",
                    },
                    "test-token",
                ),
            ]
        )
        assert expected_api.call.await_count == 2
        unused_api.call.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("has_client", [False, True])
    async def test_non_slack_turn_does_not_change_client_binding(self, has_client):
        self.context.activity.channel_id = ChannelId("msteams")
        per_turn_api = MagicMock(spec=SlackApi)
        if has_client:
            self.context.services.set(SlackApi, per_turn_api)
        SlackAgentExtension(self.app)
        handler = AsyncMock()
        self.app.message("hello")(handler)

        await self.app.on_turn(self.context)

        handler.assert_awaited_once()
        assert self.context.services.get(SlackApi) is (
            per_turn_api if has_client else None
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "event, error",
        [
            ({"ts": "thread-ts"}, "non-empty event.channel"),
            ({"channel": "", "ts": "thread-ts"}, "non-empty event.channel"),
            ({"channel": "C1"}, "non-empty thread_ts or event.ts"),
            ({"channel": "C1", "ts": ""}, "non-empty thread_ts or event.ts"),
        ],
    )
    async def test_create_stream_requires_channel_and_timestamp(self, event, error):
        api = MagicMock(spec=SlackApi)
        slack = SlackAgentExtension(self.app, slack_api=api)
        self.context.activity.channel_data = {"SlackMessage": {"event": event}}

        with pytest.raises(ValueError, match=re.escape(error)):
            await slack.create_stream(self.context)

        api.call.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_stream_accepts_explicit_timestamp_without_event_timestamp(
        self,
    ):
        api = MagicMock(spec=SlackApi)
        api.call.return_value = SlackResponse(ok=True, ts="stream-ts")
        slack = SlackAgentExtension(self.app, slack_api=api)
        self.context.activity.channel_data = {
            "SlackMessage": {"event": {"channel": "C1"}}
        }

        await slack.create_stream(self.context, thread_ts="explicit-ts")

        api.call.assert_awaited_once_with(
            "chat.startStream",
            {
                "channel": "C1",
                "thread_ts": "explicit-ts",
                "task_display_mode": "plan",
            },
            "",
        )

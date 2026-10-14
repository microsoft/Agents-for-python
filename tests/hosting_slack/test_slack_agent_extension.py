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
    ConversationUpdateTypes,
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


def _make_app() -> AgentApplication:
    app = AgentApplication(
        storage=MemoryStorage(),
        connection_manager=MagicMock(spec=Connections),
    )
    app.routes = []
    original_add_route = app.add_route

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
        original_add_route(
            selector,
            handler,
            is_invoke=is_invoke,
            rank=rank,
            auth_handlers=auth_handlers,
        )

    app.add_route = _add_route
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
        assert sel(
            _make_context(ActivityTypes.message, channel_id="slack:sub", text="hello")
        )
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


@pytest.mark.parametrize("route_name", ["message", "event"])
class TestRoutingContracts:
    @pytest.mark.parametrize(
        "select, value, matches",
        [
            ("hello", "hello", True),
            ("hello", "HELLO", False),
            ("hello", "say hello", False),
            ("hello", None, False),
            (re.compile("hello"), "hello", True),
            (re.compile("hello"), "say hello", False),
            (re.compile("hello"), "hello there", False),
            (re.compile("hello"), None, False),
            (re.compile("hello", re.IGNORECASE), "HELLO", True),
            (None, None, True),
        ],
    )
    def test_selector_contract(self, route_name, select, value, matches):
        app = _make_app()
        slack = SlackAgentExtension(app)
        register = slack.message if route_name == "message" else slack.event
        register(select)(AsyncMock())
        context = _make_context(
            route_name,
            text=value if route_name == "message" else "unrelated",
            name=value if route_name == "event" else "unrelated",
        )

        assert app.routes[-1]["selector"](context) is matches

    @pytest.mark.parametrize("select", [None, "hello"])
    def test_registration_preserves_auth_handlers_and_explicit_rank(
        self, route_name, select
    ):
        app = _make_app()
        slack = SlackAgentExtension(app)
        register = slack.message if route_name == "message" else slack.event
        handler = AsyncMock()
        auth_handlers = ["primary", "secondary"]

        returned = register(select, auth_handlers=auth_handlers, rank=RouteRank.FIRST)(
            handler
        )

        assert returned is handler
        assert app.routes[-1]["auth_handlers"] == auth_handlers
        assert app.routes[-1]["rank"] == RouteRank.FIRST


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

    @pytest.mark.parametrize("route_name", ["message", "event"])
    @pytest.mark.parametrize("select", [None, "hello"])
    def test_alias_forwards_registration_options(self, route_name, select):
        register = (
            self.slack.on_message if route_name == "message" else self.slack.on_event
        )
        handler = AsyncMock()
        auth_handlers = ["primary", "secondary"]

        with pytest.deprecated_call():
            returned = register(
                select, auth_handlers=auth_handlers, rank=RouteRank.FIRST
            )(handler)

        assert returned is handler
        assert len(self.app.routes) == 1
        assert self.app.routes[-1]["auth_handlers"] == auth_handlers
        assert self.app.routes[-1]["rank"] == RouteRank.FIRST

    @pytest.mark.parametrize("route_name", ["message", "event"])
    def test_alias_without_select_defaults_to_last_rank(self, route_name):
        register = (
            self.slack.on_message if route_name == "message" else self.slack.on_event
        )

        with pytest.deprecated_call():
            register()(AsyncMock())

        assert self.app.routes[-1]["rank"] == RouteRank.LAST


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


class TestDefaultClient:
    def test_default_client_can_be_accessed_without_running_event_loop(self):
        slack = SlackAgentExtension(_make_app())

        client = slack.slack_api

        assert isinstance(client, SlackApi)
        assert slack.slack_api is client
        assert client._session is None

    def test_construction_is_lazy_and_property_caches_client(self, monkeypatch):
        client = MagicMock(spec=SlackApi)
        factory = MagicMock(return_value=client)
        monkeypatch.setattr(
            "microsoft_agents.hosting.slack.slack_agent_extension.SlackApi", factory
        )

        slack = SlackAgentExtension(_make_app())

        factory.assert_not_called()
        assert slack.slack_api is client
        assert slack.slack_api is client
        factory.assert_called_once_with()

    def test_injected_client_does_not_create_default(self, monkeypatch):
        client = MagicMock(spec=SlackApi)
        factory = MagicMock()
        monkeypatch.setattr(
            "microsoft_agents.hosting.slack.slack_agent_extension.SlackApi", factory
        )

        slack = SlackAgentExtension(_make_app(), slack_api=client)

        assert slack.slack_api is client
        factory.assert_not_called()


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

    @pytest.mark.parametrize("original_first", [False, True])
    def test_wrapped_context_shares_streaming_response(self, original_first):
        original_response = self.context.streaming_response if original_first else None
        wrapped = SlackTurnContext(self.context, self.app)

        response = wrapped.streaming_response

        assert response is self.context.streaming_response
        assert wrapped.streaming_response is response
        if original_first:
            assert response is original_response

    def test_wrapped_context_without_registered_client_returns_none(self):
        wrapped = SlackTurnContext(self.context, self.app)

        assert wrapped.client is None
        assert not self.context.services.has(SlackApi)

    def test_wrapped_context_rejects_activity_replacement(self):
        wrapped = SlackTurnContext(self.context, self.app)
        activity = wrapped.activity

        with pytest.raises(
            NotImplementedError, match="Directly setting the activity is not supported"
        ):
            wrapped.activity = Activity(type=ActivityTypes.message)

        assert wrapped.activity is activity
        assert self.context.activity is activity

    def test_wrapped_context_preserves_slack_activity_subclasses(self):
        class CustomSlackActivity(SlackActivity):
            custom_id: str

        activity = CustomSlackActivity(
            type=ActivityTypes.message,
            channel_id=ChannelId("slack"),
            custom_id="custom",
            channel_data={"Payload": {"channel": {"id": "C1"}}},
        )
        self.context.activity = activity

        wrapped = SlackTurnContext(self.context, self.app)

        assert wrapped.activity is activity
        assert isinstance(wrapped.activity, CustomSlackActivity)
        assert wrapped.activity.model_dump()["custom_id"] == "custom"
        assert wrapped.activity.slack_channel_data.channel == "C1"

    @pytest.mark.parametrize("set_on_wrapper", [False, True])
    def test_wrapped_context_shares_responded_state(self, set_on_wrapper):
        wrapped = SlackTurnContext(self.context, self.app)
        assert wrapped.responded is False
        assert self.context.responded is False

        if set_on_wrapper:
            wrapped.responded = True
        else:
            self.context.responded = True

        assert wrapped.responded is True
        assert self.context.responded is True

    def test_wrapped_context_preserves_responded_setter_validation(self):
        wrapped = SlackTurnContext(self.context, self.app)
        wrapped.responded = True

        with pytest.raises(
            ValueError, match="cannot set TurnContext.responded to False"
        ):
            wrapped.responded = False

        assert wrapped.responded is True
        assert self.context.responded is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("route_name", ["message", "event"])
    async def test_registered_handler_receives_slack_context(self, route_name):
        app = _make_app()
        slack = SlackAgentExtension(app)
        client = MagicMock(spec=SlackApi)
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
        slack = SlackAgentExtension(self.app, slack_api=MagicMock(spec=SlackApi))
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
    @pytest.mark.parametrize("operation", ["call", "create_stream"])
    async def test_helpers_create_default_client_before_first_turn(
        self, monkeypatch, operation
    ):
        call_api = AsyncMock(return_value=SlackResponse(ok=True, ts="stream-ts"))
        monkeypatch.setattr(SlackApi, "call", call_api)
        slack = SlackAgentExtension(self.app)
        self.context.activity.channel_data = {
            "SlackMessage": {"event": {"channel": "C1", "ts": "thread-ts"}},
            "ApiToken": "test-token",
        }

        try:
            if operation == "call":
                result = await slack.call(self.context, "auth.test")
                assert result is call_api.return_value
                call_api.assert_awaited_once_with("auth.test", None, "")
            else:
                await slack.create_stream(self.context)
                call_api.assert_awaited_once_with(
                    "chat.startStream",
                    {
                        "channel": "C1",
                        "thread_ts": "thread-ts",
                        "task_display_mode": "plan",
                    },
                    "test-token",
                )

            client = slack.slack_api
            await self.app.on_turn(self.context)
            assert self.context.services.get(SlackApi) is client
            assert slack.slack_api is client
        finally:
            await slack.slack_api.aclose()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ["call", "create_stream"])
    async def test_helpers_use_per_turn_client_without_creating_default(
        self, monkeypatch, operation
    ):
        factory = MagicMock(side_effect=AssertionError("Unexpected default session"))
        monkeypatch.setattr(
            "microsoft_agents.hosting.slack.api.slack_api.ClientSession", factory
        )
        client = MagicMock(spec=SlackApi)
        client.call.return_value = SlackResponse(ok=True, ts="stream-ts")
        self.context.services.set(SlackApi, client)
        self.context.activity.channel_data = {
            "SlackMessage": {"event": {"channel": "C1", "ts": "thread-ts"}}
        }
        slack = SlackAgentExtension(self.app)

        if operation == "call":
            await slack.call(self.context, "auth.test")
        else:
            await slack.create_stream(self.context)
        await self.app.on_turn(self.context)

        client.call.assert_awaited_once()
        assert self.context.services.get(SlackApi) is client
        factory.assert_not_called()

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


def _make_activity_context(channel_id: str = "slack", **activity_fields) -> TurnContext:
    activity = Activity(
        channel_id=channel_id,
        service_url="https://example.invalid",
        conversation=ConversationAccount(id="conversation"),
        from_property=ChannelAccount(id="user"),
        recipient=ChannelAccount(id="bot"),
        **activity_fields,
    )
    return TurnContext(ChannelServiceAdapter(None), activity)


_APP_ROUTE_CASES = [
    (
        "conversation_update",
        (ConversationUpdateTypes.MEMBERS_ADDED,),
        dict(
            type=ActivityTypes.conversation_update,
            members_added=[ChannelAccount(id="new-user")],
        ),
    ),
    (
        "members_added",
        (),
        dict(
            type=ActivityTypes.conversation_update,
            members_added=[ChannelAccount(id="new-user")],
        ),
    ),
    (
        "members_removed",
        (),
        dict(
            type=ActivityTypes.conversation_update,
            members_removed=[ChannelAccount(id="old-user")],
        ),
    ),
    (
        "installation_update",
        (),
        dict(type=ActivityTypes.installation_update),
    ),
]


class TestAppRouteHooks:
    @pytest.mark.parametrize("route_name, route_args, fields", _APP_ROUTE_CASES)
    def test_selector_matches_only_slack(self, route_name, route_args, fields):
        app = _make_app()
        slack = SlackAgentExtension(app)

        async def handler(context, state):
            pass

        assert getattr(slack, route_name)(*route_args)(handler) is handler

        selector = app.routes[-1]["selector"]
        assert selector(_make_activity_context(**fields))
        assert selector(_make_activity_context(channel_id="slack:sub", **fields))
        assert not selector(_make_activity_context(channel_id="msteams", **fields))

    @pytest.mark.parametrize("route_name, route_args, fields", _APP_ROUTE_CASES)
    def test_selector_rejects_non_matching_activity(
        self, route_name, route_args, fields
    ):
        app = _make_app()
        slack = SlackAgentExtension(app)

        @getattr(slack, route_name)(*route_args)
        async def handler(context, state):
            pass

        selector = app.routes[-1]["selector"]
        assert not selector(_make_activity_context(type=ActivityTypes.message))

    @pytest.mark.parametrize(
        "route_name, other_fields",
        [
            (
                "members_added",
                dict(
                    type=ActivityTypes.conversation_update,
                    members_removed=[ChannelAccount(id="old-user")],
                ),
            ),
            (
                "members_removed",
                dict(
                    type=ActivityTypes.conversation_update,
                    members_added=[ChannelAccount(id="new-user")],
                ),
            ),
        ],
    )
    def test_member_routes_reject_opposite_update(self, route_name, other_fields):
        app = _make_app()
        slack = SlackAgentExtension(app)

        @getattr(slack, route_name)()
        async def handler(context, state):
            pass

        selector = app.routes[-1]["selector"]
        assert not selector(_make_activity_context(**other_fields))

    @pytest.mark.parametrize("route_name, route_args, fields", _APP_ROUTE_CASES)
    def test_registration_forwards_auth_handlers_and_rank(
        self, route_name, route_args, fields
    ):
        app = _make_app()
        slack = SlackAgentExtension(app)

        @getattr(slack, route_name)(
            *route_args, auth_handlers=["graph"], rank=RouteRank.FIRST
        )
        async def handler(context, state):
            pass

        route = app.routes[-1]
        assert route["auth_handlers"] == ["graph"]
        assert route["rank"] == RouteRank.FIRST

    @pytest.mark.asyncio
    @pytest.mark.parametrize("route_name, route_args, fields", _APP_ROUTE_CASES)
    async def test_handler_receives_slack_context(self, route_name, route_args, fields):
        app = _make_app()
        slack = SlackAgentExtension(app)
        context = _make_activity_context(**fields)
        state = TurnState()

        async def handler(slack_context, received_state):
            assert isinstance(slack_context, SlackTurnContext)
            assert isinstance(slack_context.activity, SlackActivity)
            assert received_state is state

        delegate = AsyncMock(side_effect=handler)
        getattr(slack, route_name)(*route_args)(delegate)

        await app.routes[-1]["handler"](context, state)

        delegate.assert_awaited_once()

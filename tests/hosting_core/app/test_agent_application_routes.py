"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import re

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import MemoryStorage, TurnContext
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    RouteRank,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth import Authorization
from tests._common.testing_objects import TestingConnectionManager as _ConnectionManager


class _StubAdapter:
    def __init__(self):
        self.sent_activities: list[Activity] = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [None] * len(activities)


def _make_app() -> AgentApplication[TurnState]:
    storage = MemoryStorage()
    return AgentApplication[TurnState](
        options=ApplicationOptions(storage=storage),
        authorization=Authorization(
            storage=storage,
            connection_manager=_ConnectionManager(),
        ),
    )


def _make_activity(channel_id: str = "test", **kwargs) -> Activity:
def _make_activity(channel_id: str = "test", **kwargs) -> Activity:
    return Activity(
        channel_id=channel_id,
        channel_id=channel_id,
        conversation={"id": "conv1"},
        from_property={"id": "user1"},
        recipient={"id": "bot1"},
        service_url="https://test",
        **kwargs,
    )


def _make_context(
    activity: Activity, adapter: _StubAdapter | None = None
) -> TurnContext:
    return TurnContext(adapter or _StubAdapter(), activity)


class TestActivityRoute:
    def setup_method(self):
        self.app = _make_app()
        self.called = False
        self.received_type: str | None = None

    @pytest.mark.asyncio
    async def test_string_match(self):
        @self.app.activity("event")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True
            self.received_type = context.activity.type

        await self.app._on_activity(
            _make_context(_make_activity(type="event")), TurnState()
        )
        assert self.called
        assert self.received_type == "event"

    @pytest.mark.asyncio
    async def test_string_no_match(self):
        @self.app.activity("event")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type="message")), TurnState()
        )
        assert not self.called

    @pytest.mark.asyncio
    async def test_activity_types_enum_match(self):
        @self.app.activity(ActivityTypes.invoke)
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.invoke)), TurnState()
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_first_element_matches(self):
        @self.app.activity(["event", ActivityTypes.message])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type="event")), TurnState()
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_second_element_matches(self):
        @self.app.activity(["event", ActivityTypes.message])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message)), TurnState()
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_no_match(self):
        @self.app.activity(["event", ActivityTypes.message])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type="invoke")), TurnState()
        )
        assert not self.called

    def test_decorator_returns_original_handler(self):
        async def handler(context: TurnContext, state: TurnState):
            pass

        result = self.app.activity("event")(handler)
        assert result is handler


class TestMessageRoute:
    def setup_method(self):
        self.app = _make_app()
        self.called = False
        self.received_text: str | None = None

    @pytest.mark.asyncio
    async def test_string_exact_match(self):
        @self.app.message("hello")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True
            self.received_text = context.activity.text

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.called
        assert self.received_text == "hello"

    @pytest.mark.asyncio
    async def test_string_no_match(self):
        @self.app.message("hello")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="world")),
            TurnState(),
        )
        assert not self.called

    @pytest.mark.asyncio
    async def test_non_message_activity_is_ignored(self):
        @self.app.message("hello")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type="event", text="hello")),
            TurnState(),
        )
        assert not self.called

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text", ["anything", None])
    async def test_none_select_matches_any_message(self, text):
        @self.app.message(None)
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text=text)),
            TurnState(),
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_none_select_ignores_non_message_activity(self):
        @self.app.message(None)
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type="event", text="hello")),
            TurnState(),
        )
        assert not self.called

    @pytest.mark.asyncio
    async def test_pattern_match(self):
        @self.app.message(re.compile(r"hello.*"))
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(type=ActivityTypes.message, text="hello world")
            ),
            TurnState(),
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_pattern_no_match(self):
        @self.app.message(re.compile(r"hello.*"))
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="bye world")),
            TurnState(),
        )
        assert not self.called

    @pytest.mark.asyncio
    async def test_list_string_match(self):
        @self.app.message(["hi", "hello", "hey"])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_pattern_match(self):
        @self.app.message([re.compile(r"hi.*"), re.compile(r"bye.*")])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(type=ActivityTypes.message, text="bye everyone")
            ),
            TurnState(),
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_mixed_string_and_pattern_match(self):
        @self.app.message(["hello", re.compile(r"bye.*")])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="bye world")),
            TurnState(),
        )
        assert self.called

    @pytest.mark.asyncio
    async def test_list_no_match(self):
        @self.app.message(["hello", re.compile(r"bye.*")])
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="greetings")),
            TurnState(),
        )
        assert not self.called

    def test_decorator_returns_original_handler(self):
        async def handler(context: TurnContext, state: TurnState):
            pass

        result = self.app.message("hello")(handler)
        assert result is handler


class TestHandoffRoute:
    def setup_method(self):
        self.adapter = _StubAdapter()
        self.app = _make_app()
        self.received_continuation: str | None = None

    def _handoff_context(self, continuation: str = "cont123") -> TurnContext:
        return TurnContext(
            self.adapter,
            _make_activity(
                type=ActivityTypes.invoke,
                name="handoff/action",
                value={"continuation": continuation},
            ),
        )

    @pytest.mark.asyncio
    async def test_factory_style_routes_correctly(self):
        @self.app.handoff()
        async def handler(context, state, continuation):
            self.received_continuation = continuation

        await self.app._on_activity(self._handoff_context("abc"), TurnState())
        assert self.received_continuation == "abc"

    @pytest.mark.asyncio
    async def test_direct_style_routes_correctly(self):
        @self.app.handoff
        async def handler(context, state, continuation):
            self.received_continuation = continuation

        await self.app._on_activity(self._handoff_context("xyz"), TurnState())
        assert self.received_continuation == "xyz"

    @pytest.mark.asyncio
    async def test_sends_invoke_response(self):
        """The route wrapper must send a 200 invoke response regardless of func's return value."""

        @self.app.handoff
        async def handler(context, state, continuation):
            pass

        await self.app._on_activity(self._handoff_context(), TurnState())

        invoke_responses = [
            a
            for a in self.adapter.sent_activities
            if a.type == ActivityTypes.invoke_response
        ]
        assert len(invoke_responses) == 1
        from microsoft_agents.activity import InvokeResponse

        value = invoke_responses[0].value
        assert isinstance(value, InvokeResponse)
        assert value.status == 200

    @pytest.mark.asyncio
    async def test_does_not_match_other_invoke_names(self):
        @self.app.handoff
        async def handler(context, state, continuation):
            self.received_continuation = continuation

        ctx = TurnContext(
            self.adapter,
            _make_activity(type=ActivityTypes.invoke, name="other/action"),
        )
        await self.app._on_activity(ctx, TurnState())
        assert self.received_continuation is None

    @pytest.mark.asyncio
    async def test_does_not_match_non_invoke(self):
        @self.app.handoff
        async def handler(context, state, continuation):
            self.received_continuation = continuation

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.received_continuation is None

    def test_factory_style_returns_original_handler(self):
        async def handler(context, state, continuation):
            pass

        result = self.app.handoff()(handler)
        assert result is handler

    def test_direct_style_returns_original_handler(self):
        async def handler(context, state, continuation):
            pass

        result = self.app.handoff(handler)
        assert result is handler


class TestRouteOrdering:
    def setup_method(self):
        self.app = _make_app()
        self.call_order: list[str] = []

    @pytest.mark.asyncio
    async def test_only_first_matching_route_fires(self):
        @self.app.message("hello")
        async def first(context: TurnContext, state: TurnState):
            self.call_order.append("first")

        @self.app.message("hello")
        async def second(context: TurnContext, state: TurnState):
            self.call_order.append("second")

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.call_order == ["first"]

    @pytest.mark.asyncio
    async def test_non_matching_route_is_skipped(self):
        @self.app.message("bye")
        async def first(context: TurnContext, state: TurnState):
            self.call_order.append("first")

        @self.app.message("hello")
        async def second(context: TurnContext, state: TurnState):
            self.call_order.append("second")

        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.call_order == ["second"]

    @pytest.mark.asyncio
    async def test_multiple_routes_different_types_each_fires_for_own_activity(self):
        @self.app.message("hello")
        async def msg_handler(context: TurnContext, state: TurnState):
            self.call_order.append("message")

        @self.app.activity("event")
        async def evt_handler(context: TurnContext, state: TurnState):
            self.call_order.append("event")

        await self.app._on_activity(
            _make_context(_make_activity(type="event")), TurnState()
        )
        await self.app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert self.call_order == ["event", "message"]


class TestChannelIdRouteFiltering:
    def setup_method(self):
        self.app = _make_app()
        self.called = False

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("webchat", False)],
    )
    @pytest.mark.asyncio
    async def test_activity_route_filters_by_channel_id(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.activity("event", channel_id="msteams")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(_make_activity(channel_id=incoming_channel_id, type="event")),
            TurnState(),
        )
        assert self.called is expected

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("msteams:meeting", False)],
    )
    @pytest.mark.asyncio
    async def test_message_route_filters_by_exact_subchannel(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.message("hello", channel_id="msteams:copilot")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(
                    channel_id=incoming_channel_id,
                    type=ActivityTypes.message,
                    text="hello",
                )
            ),
            TurnState(),
        )
        assert self.called is expected

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("webchat", False)],
    )
    @pytest.mark.asyncio
    async def test_conversation_update_route_filters_by_channel_id(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.conversation_update("membersAdded", channel_id="msteams")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(
                    channel_id=incoming_channel_id,
                    type=ActivityTypes.conversation_update,
                    members_added=[{"id": "new-member"}],
                )
            ),
            TurnState(),
        )
        assert self.called is expected

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("msteams:meeting", False)],
    )
    @pytest.mark.asyncio
    async def test_message_reaction_route_filters_by_exact_subchannel(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.message_reaction("reactionsAdded", channel_id="msteams:copilot")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(
                    channel_id=incoming_channel_id,
                    type=ActivityTypes.message_reaction,
                    reactions_added=[{"type": "like"}],
                )
            ),
            TurnState(),
        )
        assert self.called is expected

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("webchat", False)],
    )
    @pytest.mark.asyncio
    async def test_message_update_route_filters_by_channel_id(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.message_update("editMessage", channel_id="msteams")
        async def handler(context: TurnContext, state: TurnState):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(
                    channel_id=incoming_channel_id,
                    type=ActivityTypes.message_update,
                    channel_data={"event_type": "editMessage"},
                )
            ),
            TurnState(),
        )
        assert self.called is expected

    @pytest.mark.parametrize(
        ("incoming_channel_id", "expected"),
        [("msteams:copilot", True), ("msteams:meeting", False)],
    )
    @pytest.mark.asyncio
    async def test_handoff_route_filters_by_exact_subchannel(
        self, incoming_channel_id: str, expected: bool
    ):
        @self.app.handoff(channel_id="msteams:copilot")
        async def handler(context, state, continuation):
            self.called = True

        await self.app._on_activity(
            _make_context(
                _make_activity(
                    channel_id=incoming_channel_id,
                    type=ActivityTypes.invoke,
                    name="handoff/action",
                    value={"continuation": "cont123"},
                )
            ),
            TurnState(),
        )
        assert self.called is expected


def _only_route(app: AgentApplication):
    routes = list(app._route_list)
    assert len(routes) == 1
    return routes[0]


async def _noop(context: TurnContext, state: TurnState):
    pass


class TestEventRoute:
    def setup_method(self):
        self.app = _make_app()

    @pytest.mark.parametrize(
        ("select", "name", "expected"),
        [
            ("ping", "ping", True),
            ("ping", "pong", False),
            (re.compile(r"app_.*"), "app_mention", True),
            (re.compile(r"app_.*"), "message", False),
            (["ping", re.compile(r"app_.*")], "app_mention", True),
            (["ping", re.compile(r"app_.*")], "pong", False),
            (None, "anything", True),
        ],
    )
    def test_selector_matches_event_name(self, select, name, expected):
        self.app.event(select)(_noop)

        selector = _only_route(self.app).selector
        assert (
            selector(_make_context(_make_activity(type="event", name=name))) is expected
        )

    def test_selector_ignores_non_event_activity(self):
        self.app.event("ping")(_noop)

        selector = _only_route(self.app).selector
        assert not selector(
            _make_context(_make_activity(type=ActivityTypes.message, name="ping"))
        )

    @pytest.mark.parametrize(
        "activity_type", [ActivityTypes.message, ActivityTypes.invoke]
    )
    def test_none_select_ignores_non_event_activity(self, activity_type):
        self.app.event()(_noop)

        selector = _only_route(self.app).selector
        assert not selector(
            _make_context(_make_activity(type=activity_type, name="ping"))
        )

    @pytest.mark.parametrize(
        ("select", "expected_rank"),
        [(None, RouteRank.LAST), ("ping", RouteRank.DEFAULT)],
    )
    def test_default_rank(self, select, expected_rank):
        self.app.event(select)(_noop)

        assert _only_route(self.app).rank == expected_rank

    def test_explicit_rank_is_preserved_without_select(self):
        self.app.event(rank=RouteRank.FIRST)(_noop)

        assert _only_route(self.app).rank == RouteRank.FIRST

    @pytest.mark.asyncio
    async def test_dispatches_matching_event(self):
        called = []

        @self.app.event("ping")
        async def handler(context: TurnContext, state: TurnState):
            called.append(context.activity.name)

        await self.app._on_activity(
            _make_context(_make_activity(type="event", name="ping")), TurnState()
        )
        assert called == ["ping"]


class TestInvokeRoute:
    def setup_method(self):
        self.app = _make_app()

    @pytest.mark.parametrize(
        ("select", "name", "expected"),
        [
            ("task/fetch", "task/fetch", True),
            ("task/fetch", "task/submit", False),
            (re.compile(r"task/.*"), "task/submit", True),
            (["a", "task/submit"], "task/submit", True),
            (None, "anything", True),
        ],
    )
    def test_selector_matches_invoke_name(self, select, name, expected):
        self.app.invoke(select)(_noop)

        selector = _only_route(self.app).selector
        assert (
            selector(
                _make_context(_make_activity(type=ActivityTypes.invoke, name=name))
            )
            is expected
        )

    def test_selector_ignores_non_invoke_activity(self):
        self.app.invoke("task/fetch")(_noop)

        selector = _only_route(self.app).selector
        assert not selector(
            _make_context(_make_activity(type="event", name="task/fetch"))
        )

    @pytest.mark.parametrize(
        "activity_type", [ActivityTypes.message, ActivityTypes.event]
    )
    def test_none_select_ignores_non_invoke_activity(self, activity_type):
        self.app.invoke()(_noop)

        selector = _only_route(self.app).selector
        assert not selector(
            _make_context(_make_activity(type=activity_type, name="task/fetch"))
        )

    @pytest.mark.parametrize(
        ("select", "expected_rank"),
        [(None, RouteRank.LAST), ("task/fetch", RouteRank.DEFAULT)],
    )
    def test_default_rank(self, select, expected_rank):
        self.app.invoke(select)(_noop)

        assert _only_route(self.app).rank == expected_rank


class TestMessageRouteRank:
    @pytest.mark.parametrize(
        ("select", "kwargs", "expected_rank"),
        [
            (None, {}, RouteRank.LAST),
            ("hello", {}, RouteRank.DEFAULT),
            (None, {"rank": RouteRank.FIRST}, RouteRank.FIRST),
        ],
    )
    def test_rank(self, select, kwargs, expected_rank):
        app = _make_app()
        app.message(select, **kwargs)(_noop)

        assert _only_route(app).rank == expected_rank

    @pytest.mark.asyncio
    async def test_catch_all_registered_first_does_not_shadow_specific_route(self):
        app = _make_app()
        calls = []

        @app.message()
        async def catch_all(context: TurnContext, state: TurnState):
            calls.append("catch_all")

        @app.message("hello")
        async def specific(context: TurnContext, state: TurnState):
            calls.append("specific")

        await app._on_activity(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello")),
            TurnState(),
        )
        assert calls == ["specific"]


def _members_added_activity(**kwargs) -> Activity:
    return _make_activity(
        type=ActivityTypes.conversation_update, members_added=[{"id": "m"}], **kwargs
    )


def _members_removed_activity(**kwargs) -> Activity:
    return _make_activity(
        type=ActivityTypes.conversation_update, members_removed=[{"id": "m"}], **kwargs
    )


def _reactions_added_activity(**kwargs) -> Activity:
    return _make_activity(
        type=ActivityTypes.message_reaction,
        reactions_added=[{"type": "like"}],
        **kwargs,
    )


def _reactions_removed_activity(**kwargs) -> Activity:
    return _make_activity(
        type=ActivityTypes.message_reaction,
        reactions_removed=[{"type": "like"}],
        **kwargs,
    )


_SHORTCUT_ROUTE_CASES = [
    ("members_added", _members_added_activity, _members_removed_activity),
    ("members_removed", _members_removed_activity, _members_added_activity),
    ("message_reaction_added", _reactions_added_activity, _reactions_removed_activity),
    (
        "message_reactions_removed",
        _reactions_removed_activity,
        _reactions_added_activity,
    ),
    (
        "installation_update",
        lambda **kw: _make_activity(type=ActivityTypes.installation_update, **kw),
        lambda **kw: _make_activity(type=ActivityTypes.message, **kw),
    ),
    (
        "end_of_conversation",
        lambda **kw: _make_activity(type=ActivityTypes.end_of_conversation, **kw),
        lambda **kw: _make_activity(type=ActivityTypes.message, **kw),
    ),
]


class TestShortcutRoutes:
    @pytest.mark.parametrize(("route_name", "matching", "other"), _SHORTCUT_ROUTE_CASES)
    def test_selector_matches_only_its_activity(self, route_name, matching, other):
        app = _make_app()
        getattr(app, route_name)()(_noop)

        selector = _only_route(app).selector
        assert selector(_make_context(matching()))
        assert not selector(_make_context(other()))

    @pytest.mark.parametrize(("route_name", "matching", "other"), _SHORTCUT_ROUTE_CASES)
    def test_selector_filters_by_channel_id(self, route_name, matching, other):
        app = _make_app()
        getattr(app, route_name)(channel_id="msteams")(_noop)

        selector = _only_route(app).selector
        assert selector(_make_context(matching(channel_id="msteams:copilot")))
        assert not selector(_make_context(matching(channel_id="webchat")))

    @pytest.mark.parametrize(("route_name", "matching", "other"), _SHORTCUT_ROUTE_CASES)
    def test_forwards_auth_handlers_and_rank(self, route_name, matching, other):
        app = _make_app()
        getattr(app, route_name)(auth_handlers=["graph"], rank=RouteRank.FIRST)(_noop)

        route = _only_route(app)
        assert route.auth_handlers == ["graph"]
        assert route.rank == RouteRank.FIRST

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("route_name", "matching", "other"), _SHORTCUT_ROUTE_CASES)
    async def test_dispatches_matching_activity(self, route_name, matching, other):
        app = _make_app()
        calls = []

        @getattr(app, route_name)()
        async def handler(context: TurnContext, state: TurnState):
            calls.append(context.activity.type)

        await app._on_activity(_make_context(matching()), TurnState())
        assert calls == [matching().type]

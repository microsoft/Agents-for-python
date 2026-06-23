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


def _make_activity(**kwargs) -> Activity:
    return Activity(
        channel_id="test",
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

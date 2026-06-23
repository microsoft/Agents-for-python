"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    TurnState,
)
from microsoft_agents.hosting.core.app.app_error import ApplicationError
from microsoft_agents.hosting.core.app.oauth import Authorization
from tests._common.testing_objects import TestingConnectionManager as _ConnectionManager


def _make_event_activity() -> Activity:
    """Minimal event Activity with all fields required by state loading."""
    return Activity(
        type=ActivityTypes.event,
        channel_id="test_channel",
        conversation={"id": "test_conv"},
        from_property={"id": "test_user"},
    )


def _make_integration_app() -> AgentApplication:
    """AgentApplication wired for on_turn integration tests (no typing, no mention-strip)."""
    app = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=MemoryStorage(),
            start_typing_timer=False,
            remove_recipient_mention=False,
        ),
        authorization=Authorization(
            storage=MemoryStorage(),
            connection_manager=_ConnectionManager(),
        ),
    )
    # Shadow class-level lists with fresh instance-level lists for test isolation
    app._internal_before_turn = []
    app._internal_after_turn = []
    return app


class StubAdapter:
    """Minimal adapter for testing AgentApplication._on_turn."""

    def __init__(self):
        self.sent_activities: list[Activity] = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [None] * len(activities)


class StubTurnContext:
    """Minimal TurnContext double for AgentApplication tests."""

    def __init__(self, activity: Activity, adapter=None):
        self.activity = activity
        self.adapter = adapter or StubAdapter()
        self._on_send_handlers = []
        self.turn_state = {}
        self.responded = False

    def on_send_activities(self, handler):
        self._on_send_handlers.append(handler)

    async def send_activity(self, activity):
        self.responded = True


def make_auth():
    return Authorization(
        storage=MemoryStorage(),
        connection_manager=_ConnectionManager(),
    )


def make_app():
    app = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        authorization=make_auth(),
    )
    # Reset to instance-level lists to isolate tests from the class-level defaults
    app._internal_before_turn = []
    app._internal_after_turn = []
    return app


@pytest.mark.asyncio
async def test_on_turn_no_typing_when_start_typing_timer_false():
    """When start_typing_timer=False, no typing indicators should be sent."""
    adapter = StubAdapter()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=MemoryStorage(),
            start_typing_timer=False,
        ),
        authorization=make_auth(),
    )

    context = StubTurnContext(
        Activity(
            type=ActivityTypes.message,
            text="hello",
            channel_id="test",
            conversation={"id": "conv1"},
            from_property={"id": "user1"},
            recipient={"id": "bot1"},
            service_url="https://test",
        ),
        adapter=adapter,
    )

    # Patch internals to avoid needing full infrastructure
    with patch.object(app, "_remove_mentions"), patch.object(
        app, "_initialize_state", new_callable=AsyncMock, return_value=TurnState()
    ), patch.object(
        app, "_run_before_turn_middleware", new_callable=AsyncMock, return_value=True
    ), patch.object(
        app, "_handle_file_downloads", new_callable=AsyncMock
    ), patch.object(
        app, "_on_activity", new_callable=AsyncMock
    ), patch.object(
        app, "_run_after_turn_middleware", new_callable=AsyncMock, return_value=True
    ):
        await app._on_turn(context)

    # Give any background tasks a chance to fire (they shouldn't)
    await asyncio.sleep(0.1)

    # No typing activities should have been sent via adapter
    typing_activities = [
        a for a in adapter.sent_activities if a.type == ActivityTypes.typing
    ]
    assert len(typing_activities) == 0

    # No on_send_activities hook should have been registered
    assert len(context._on_send_handlers) == 0


# ---------------------------------------------------------------------------
# AgentApplication.__init__ guard: connection_manager required
# ---------------------------------------------------------------------------


def test_init_raises_without_authorization_or_connection_manager():
    with pytest.raises(ApplicationError):
        AgentApplication[TurnState](options=ApplicationOptions(storage=MemoryStorage()))


def test_init_succeeds_when_authorization_provided_without_connection_manager():
    auth = make_auth()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        authorization=auth,
    )
    assert app.auth is auth


# ---------------------------------------------------------------------------
# before_turn / after_turn – registration
# ---------------------------------------------------------------------------


def test_before_turn_registers_handler():
    app = make_app()

    async def handler(ctx, state):
        return True

    app.before_turn(handler)
    assert handler in app._internal_before_turn


def test_after_turn_registers_handler():
    app = make_app()

    async def handler(ctx, state):
        return True

    app.after_turn(handler)
    assert handler in app._internal_after_turn


def test_before_turn_multiple_handlers_preserved_in_order():
    app = make_app()

    async def first(ctx, state):
        return True

    async def second(ctx, state):
        return True

    app.before_turn(first)
    app.before_turn(second)
    assert app._internal_before_turn == [first, second]


def test_after_turn_multiple_handlers_preserved_in_order():
    app = make_app()

    async def first(ctx, state):
        return True

    async def second(ctx, state):
        return True

    app.after_turn(first)
    app.after_turn(second)
    assert app._internal_after_turn == [first, second]


# ---------------------------------------------------------------------------
# before_turn / after_turn – execution via middleware helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_before_turn_middleware_calls_handler_with_context_and_state():
    app = make_app()
    calls = []

    async def handler(ctx, state):
        calls.append((ctx, state))
        return True

    app.before_turn(handler)

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_before_turn_middleware(context, state)

    assert result is True
    assert len(calls) == 1
    assert calls[0] == (context, state)


@pytest.mark.asyncio
async def test_run_before_turn_middleware_returns_false_and_stops_on_false_handler():
    app = make_app()
    calls = []

    async def first(ctx, state):
        calls.append("first")
        return False

    async def second(ctx, state):
        calls.append("second")
        return True

    app.before_turn(first)
    app.before_turn(second)

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_before_turn_middleware(context, state)

    assert result is False
    assert calls == ["first"]


@pytest.mark.asyncio
async def test_run_before_turn_middleware_returns_true_when_no_handlers():
    app = make_app()

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_before_turn_middleware(context, state)

    assert result is True


@pytest.mark.asyncio
async def test_run_after_turn_middleware_calls_handler_with_context_and_state():
    app = make_app()
    calls = []

    async def handler(ctx, state):
        calls.append((ctx, state))
        return True

    app.after_turn(handler)

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_after_turn_middleware(context, state)

    assert result is True
    assert len(calls) == 1
    assert calls[0] == (context, state)


@pytest.mark.asyncio
async def test_run_after_turn_middleware_returns_false_and_stops_on_false_handler():
    app = make_app()
    calls = []

    async def first(ctx, state):
        calls.append("first")
        return False

    async def second(ctx, state):
        calls.append("second")
        return True

    app.after_turn(first)
    app.after_turn(second)

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_after_turn_middleware(context, state)

    assert result is False
    assert calls == ["first"]


@pytest.mark.asyncio
async def test_run_after_turn_middleware_returns_true_when_no_handlers():
    app = make_app()

    context = StubTurnContext(Activity(type=ActivityTypes.event))
    state = TurnState()
    result = await app._run_after_turn_middleware(context, state)

    assert result is True


# ---------------------------------------------------------------------------
# Integration tests: before_turn / after_turn through on_turn
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_turn_calls_before_turn_handler():
    app = _make_integration_app()
    calls = []

    async def before(ctx, state):
        calls.append("before")
        return True

    app.before_turn(before)
    await app.on_turn(StubTurnContext(_make_event_activity()))

    assert calls == ["before"]


@pytest.mark.asyncio
async def test_on_turn_calls_after_turn_handler():
    app = _make_integration_app()
    calls = []

    async def after(ctx, state):
        calls.append("after")
        return True

    app.after_turn(after)
    await app.on_turn(StubTurnContext(_make_event_activity()))

    assert calls == ["after"]


@pytest.mark.asyncio
async def test_on_turn_before_turn_false_skips_activity_handler():
    app = _make_integration_app()
    calls = []

    async def before(ctx, state):
        calls.append("before")
        return False

    app.before_turn(before)

    @app.activity(ActivityTypes.event)
    async def on_event(ctx, state):
        calls.append("event")

    await app.on_turn(StubTurnContext(_make_event_activity()))

    assert calls == ["before"]


@pytest.mark.asyncio
async def test_on_turn_execution_order_before_activity_after():
    app = _make_integration_app()
    calls = []

    async def before(ctx, state):
        calls.append("before")
        return True

    async def after(ctx, state):
        calls.append("after")
        return True

    app.before_turn(before)
    app.after_turn(after)

    @app.activity(ActivityTypes.event)
    async def on_event(ctx, state):
        calls.append("event")

    await app.on_turn(StubTurnContext(_make_event_activity()))

    assert calls == ["before", "event", "after"]


@pytest.mark.asyncio
async def test_on_turn_after_turn_false_still_runs_after_activity_handler():
    """after_turn returning False stops state save but does not prevent the activity handler."""
    app = _make_integration_app()
    calls = []

    async def after(ctx, state):
        calls.append("after")
        return False

    app.after_turn(after)

    @app.activity(ActivityTypes.event)
    async def on_event(ctx, state):
        calls.append("event")

    await app.on_turn(StubTurnContext(_make_event_activity()))

    assert calls == ["event", "after"]

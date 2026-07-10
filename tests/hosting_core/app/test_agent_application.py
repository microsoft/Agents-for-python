"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from microsoft_agents.activity import Activity, ActivityTypes, TokenResponse
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


@pytest.mark.asyncio
async def test_token_exchange_invoke_returns_before_continuation_replay_completes():
    """Token exchange must not keep the invoke open while the message is replayed."""
    app = _make_integration_app()
    replay_started = asyncio.Event()
    release_replay = asyncio.Event()
    replay_completed = asyncio.Event()

    continuation = Activity(
        type=ActivityTypes.message,
        id="message-id",
        text="hello",
        channel_id="msteams:COPILOT",
        conversation={"id": "conversation"},
        from_property={"id": "user"},
        recipient={"id": "agent"},
        service_url="https://message.example.org",
    )
    invoke = Activity(
        type=ActivityTypes.invoke,
        id="invoke-id",
        name="signin/tokenExchange",
        channel_id="msteams:COPILOT",
        conversation={"id": "conversation"},
        from_property={"id": "user"},
        recipient={"id": "agent"},
        service_url="https://invoke.example.org",
    )
    context = StubTurnContext(invoke)
    context.identity = MagicMock()
    token_response = TokenResponse(token="access-token")
    app._auth._handlers["handler"] = MagicMock()
    Authorization._cache_token(context, "handler", token_response)
    turn_state = MagicMock()
    call_order = []

    async def save_turn_state(_context):
        call_order.append("save")

    turn_state.save = AsyncMock(side_effect=save_turn_state)

    async def replay_turn(replay_context):
        assert (
            Authorization._get_cached_token(replay_context, "handler") is token_response
        )
        replay_started.set()
        await release_replay.wait()
        replay_completed.set()

    async def continue_conversation(identity, replay_activity, callback):
        call_order.append("continue")
        replay_context = StubTurnContext(replay_activity, context.adapter)
        replay_context.identity = identity
        await callback(replay_context)

    context.adapter.continue_conversation_with_claims = AsyncMock(
        side_effect=continue_conversation
    )

    original_on_turn = app._on_turn
    app.on_turn = AsyncMock(side_effect=replay_turn)
    app._on_turn = AsyncMock(side_effect=replay_turn)
    app._auth._on_turn_auth_intercept = AsyncMock(return_value=(True, continuation))

    with patch.object(
        app, "_initialize_state", new_callable=AsyncMock, return_value=turn_state
    ):
        await asyncio.wait_for(original_on_turn(context), timeout=0.1)

    await asyncio.wait_for(replay_started.wait(), timeout=0.1)
    assert not replay_completed.is_set()
    turn_state.save.assert_awaited_once_with(context)
    context.adapter.continue_conversation_with_claims.assert_awaited_once()
    replay_args = context.adapter.continue_conversation_with_claims.call_args.args
    assert replay_args[0] is context.identity
    replay_activity = replay_args[1]
    assert replay_args[2] != app._on_turn
    assert replay_activity is not continuation
    assert replay_activity.id == "message-id"
    assert replay_activity.type == ActivityTypes.message
    assert replay_activity.channel_id == "msteams:COPILOT"
    assert replay_activity.service_url == "https://invoke.example.org"
    assert context.activity.type == ActivityTypes.invoke
    assert context.activity.id == "invoke-id"
    assert context.activity.channel_id == "msteams:COPILOT"
    assert call_order[:2] == ["save", "continue"]
    app.on_turn.assert_not_awaited()

    release_replay.set()
    await asyncio.wait_for(replay_completed.wait(), timeout=0.1)


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


# ---------------------------------------------------------------------------
# connection_manager property and constructor guard
# ---------------------------------------------------------------------------


def test_init_raises_when_both_authorization_and_connection_manager_provided():
    """Providing both authorization and connection_manager is ambiguous and should raise."""
    with pytest.raises(ApplicationError):
        AgentApplication[TurnState](
            options=ApplicationOptions(storage=MemoryStorage()),
            authorization=make_auth(),
            connection_manager=_ConnectionManager(),
        )


def test_connection_manager_property_returns_manager_from_authorization():
    """When authorization is provided, connection_manager property reflects auth's manager."""
    cm = _ConnectionManager()
    auth = Authorization(storage=MemoryStorage(), connection_manager=cm)
    app = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        authorization=auth,
    )
    assert app.connection_manager is cm


def test_connection_manager_property_returns_directly_passed_manager():
    """When connection_manager kwarg is used (no authorization), the property returns it."""
    cm = _ConnectionManager()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=cm,
    )
    assert app.connection_manager is cm


def test_init_with_connection_manager_only_creates_auth():
    """Passing only connection_manager should auto-create an Authorization instance."""
    cm = _ConnectionManager()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=cm,
    )
    assert app.auth is not None
    assert app.connection_manager is cm

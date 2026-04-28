"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationParameters,
    ConversationReference,
    ResourceResponse,
)
from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.app.proactive import (
    Conversation,
    CreateConversationOptions,
    Proactive,
    ProactiveOptions,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reference(
    conversation_id="conv-1",
    service_url="https://smba.trafficmanager.net/teams/",
    channel_id="msteams",
):
    # bot and user must be present: get_continuation_activity() passes them directly
    # to Activity(recipient=..., from_property=...) which rejects explicit None values.
    return ConversationReference(
        conversation=ConversationAccount(id=conversation_id),
        service_url=service_url,
        channel_id=channel_id,
        bot=ChannelAccount(id="28:bot-id"),
        user=ChannelAccount(id="user-id"),
    )


def _make_conversation(conversation_id="conv-1"):
    return Conversation(
        claims={"aud": "app-id", "tid": "tenant"},
        conversation_reference=_make_reference(conversation_id),
    )


def _make_app(storage=None):
    app = MagicMock()
    app.options.storage = storage
    app._turn_state_factory = None
    app._auth = None
    return app


def _make_mock_state():
    state = MagicMock()
    state.save = AsyncMock()
    state.load = AsyncMock()
    return state


# ---------------------------------------------------------------------------
# Storage property
# ---------------------------------------------------------------------------


class TestProactiveStorageProperty:
    def test_storage_resolved_from_proactive_options(self):
        storage = MemoryStorage()
        app = _make_app(storage=None)
        opts = ProactiveOptions(storage=storage)
        proactive = Proactive(app, opts)
        assert proactive._storage is storage

    def test_storage_resolved_from_app_options(self):
        storage = MemoryStorage()
        app = _make_app(storage=storage)
        opts = ProactiveOptions()
        proactive = Proactive(app, opts)
        assert proactive._storage is storage

    def test_proactive_options_storage_takes_precedence(self):
        storage_app = MemoryStorage()
        storage_opts = MemoryStorage()
        app = _make_app(storage=storage_app)
        opts = ProactiveOptions(storage=storage_opts)
        proactive = Proactive(app, opts)
        assert proactive._storage is storage_opts

    def test_storage_raises_runtime_error_when_missing(self):
        app = _make_app(storage=None)
        opts = ProactiveOptions()
        proactive = Proactive(app, opts)
        with pytest.raises(RuntimeError):
            _ = proactive._storage


class TestProactiveStorageKey:
    def test_storage_key_format(self):
        key = Proactive._storage_key("conv-123")
        assert key == "proactive/conversations/conv-123"

    def test_storage_key_includes_conversation_id(self):
        key = Proactive._storage_key("my-unique-id")
        assert "my-unique-id" in key


# ---------------------------------------------------------------------------
# Store / Get / Delete conversations
# ---------------------------------------------------------------------------


class TestProactiveStoreConversation:
    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def proactive(self, storage):
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    @pytest.mark.asyncio
    async def test_store_then_get_returns_conversation(self, proactive):
        conv = _make_conversation("store-get")
        await proactive.store_conversation(conv)
        result = await proactive.get_conversation("store-get")
        assert result is not None
        assert result.conversation_reference.conversation.id == "store-get"

    @pytest.mark.asyncio
    async def test_store_preserves_claims(self, proactive):
        conv = _make_conversation("claims-test")
        await proactive.store_conversation(conv)
        result = await proactive.get_conversation("claims-test")
        assert result.claims.get("aud") == "app-id"
        assert result.claims.get("tid") == "tenant"

    @pytest.mark.asyncio
    async def test_store_overwrites_existing_conversation(self, proactive):
        await proactive.store_conversation(_make_conversation("overwrite-me"))
        new_conv = Conversation(
            claims={"aud": "new-app-id"},
            conversation_reference=_make_reference("overwrite-me"),
        )
        await proactive.store_conversation(new_conv)
        result = await proactive.get_conversation("overwrite-me")
        assert result.claims.get("aud") == "new-app-id"

    @pytest.mark.asyncio
    async def test_store_from_turn_context(self, proactive):
        ref = _make_reference("ctx-conv")
        identity = ClaimsIdentity(claims={"aud": "ctx-app"}, is_authenticated=True)

        # spec=TurnContext is required: store_conversation checks isinstance(ctx, TurnContext)
        ctx = MagicMock(spec=TurnContext)
        ctx.activity = MagicMock()
        ctx.activity.get_conversation_reference.return_value = ref
        ctx.turn_state = {ChannelAdapter.AGENT_IDENTITY_KEY: identity}

        await proactive.store_conversation(ctx)
        result = await proactive.get_conversation("ctx-conv")
        assert result is not None
        assert result.claims.get("aud") == "ctx-app"


class TestProactiveGetConversation:
    @pytest.fixture
    def proactive(self):
        storage = MemoryStorage()
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, proactive):
        result = await proactive.get_conversation("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_after_delete(self, proactive):
        await proactive.store_conversation(_make_conversation("to-delete"))
        await proactive.delete_conversation("to-delete")
        result = await proactive.get_conversation("to-delete")
        assert result is None


class TestProactiveDeleteConversation:
    @pytest.fixture
    def proactive(self):
        storage = MemoryStorage()
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    @pytest.mark.asyncio
    async def test_delete_removes_stored_conversation(self, proactive):
        await proactive.store_conversation(_make_conversation("del-conv"))
        await proactive.delete_conversation("del-conv")
        assert await proactive.get_conversation("del-conv") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_does_not_raise(self, proactive):
        await proactive.delete_conversation("not-stored")  # must not raise

    @pytest.mark.asyncio
    async def test_delete_only_removes_target(self, proactive):
        await proactive.store_conversation(_make_conversation("keep-me"))
        await proactive.store_conversation(_make_conversation("remove-me"))
        await proactive.delete_conversation("remove-me")
        assert await proactive.get_conversation("keep-me") is not None
        assert await proactive.get_conversation("remove-me") is None


# ---------------------------------------------------------------------------
# Send activity
# ---------------------------------------------------------------------------


class TestProactiveSendActivity:
    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def proactive(self, storage):
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    def _make_adapter(self, response_id="resp-1"):
        adapter = MagicMock()

        async def fake_continue(claims, continuation, callback):
            ctx = MagicMock()
            ctx.send_activity = AsyncMock(return_value=ResourceResponse(id=response_id))
            await callback(ctx)

        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)
        return adapter

    @pytest.mark.asyncio
    async def test_send_activity_with_conversation_object(self, proactive):
        conv = _make_conversation("send-obj")
        adapter = self._make_adapter()
        activity = Activity(type=ActivityTypes.message, text="Hello!")
        await proactive.send_activity(adapter, conv, activity)
        adapter.continue_conversation_with_claims.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_activity_with_conversation_id(self, proactive):
        conv = _make_conversation("send-id")
        await proactive.store_conversation(conv)
        adapter = self._make_adapter()
        activity = Activity(type=ActivityTypes.message, text="Notify!")
        await proactive.send_activity(adapter, "send-id", activity)
        adapter.continue_conversation_with_claims.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_activity_raises_for_missing_conversation(self, proactive):
        adapter = self._make_adapter()
        activity = Activity(type=ActivityTypes.message, text="Hello")
        with pytest.raises(KeyError):
            await proactive.send_activity(adapter, "no-such-conv", activity)

    @pytest.mark.asyncio
    async def test_send_activity_passes_activity_to_adapter(self, proactive):
        conv = _make_conversation("pass-activity")
        sent_activity = None

        async def fake_continue(claims, continuation, callback):
            nonlocal sent_activity
            ctx = MagicMock()

            async def capture_send(act):
                nonlocal sent_activity
                sent_activity = act
                return ResourceResponse(id="r")

            ctx.send_activity = capture_send
            await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)
        activity = Activity(type=ActivityTypes.message, text="Specific text")
        await proactive.send_activity(adapter, conv, activity)
        assert sent_activity is activity

    @pytest.mark.asyncio
    async def test_send_activity_propagates_exception_from_callback(self, proactive):
        conv = _make_conversation("exc-conv")

        async def fake_continue(claims, continuation, callback):
            ctx = MagicMock()
            ctx.send_activity = AsyncMock(side_effect=RuntimeError("channel error"))
            await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)
        with pytest.raises(RuntimeError, match="channel error"):
            await proactive.send_activity(
                adapter, conv, Activity(type=ActivityTypes.message)
            )


# ---------------------------------------------------------------------------
# Continue conversation
# ---------------------------------------------------------------------------


class TestProactiveContinueConversation:
    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def proactive(self, storage):
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    def _make_adapter(self, proactive_instance, state=None):
        state = state or _make_mock_state()

        async def fake_continue(claims, continuation, callback):
            ctx = MagicMock()
            with patch.object(
                proactive_instance, "_load_state", AsyncMock(return_value=state)
            ):
                await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)
        return adapter, state

    @pytest.mark.asyncio
    async def test_continue_invokes_handler(self, proactive):
        conv = _make_conversation("cont-invoke")
        handler_called = False

        async def handler(ctx, state):
            nonlocal handler_called
            handler_called = True

        adapter, _ = self._make_adapter(proactive)
        await proactive.continue_conversation(adapter, conv, handler)
        assert handler_called

    @pytest.mark.asyncio
    async def test_continue_with_conversation_id(self, proactive):
        conv = _make_conversation("cont-by-id")
        await proactive.store_conversation(conv)

        handler_called = False

        async def handler(ctx, state):
            nonlocal handler_called
            handler_called = True

        adapter, _ = self._make_adapter(proactive)
        await proactive.continue_conversation(adapter, "cont-by-id", handler)
        assert handler_called

    @pytest.mark.asyncio
    async def test_continue_raises_key_error_for_missing(self, proactive):
        async def handler(ctx, state):
            pass

        adapter = MagicMock()
        with pytest.raises(KeyError):
            await proactive.continue_conversation(adapter, "not-in-storage", handler)

    @pytest.mark.asyncio
    async def test_continue_uses_default_continuation_activity(self, proactive):
        conv = _make_conversation("default-act")
        captured_continuation = None

        async def fake_continue(claims, continuation, callback):
            nonlocal captured_continuation
            captured_continuation = continuation
            state = _make_mock_state()
            ctx = MagicMock()
            with patch.object(proactive, "_load_state", AsyncMock(return_value=state)):
                await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)

        async def handler(ctx, state):
            pass

        await proactive.continue_conversation(adapter, conv, handler)
        default_act = conv.conversation_reference.get_continuation_activity()
        assert captured_continuation.type == default_act.type

    @pytest.mark.asyncio
    async def test_continue_uses_custom_continuation_activity(self, proactive):
        conv = _make_conversation("custom-act")
        custom_activity = Activity(type=ActivityTypes.event, name="custom.event")
        captured_continuation = None

        async def fake_continue(claims, continuation, callback):
            nonlocal captured_continuation
            captured_continuation = continuation
            state = _make_mock_state()
            ctx = MagicMock()
            with patch.object(proactive, "_load_state", AsyncMock(return_value=state)):
                await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)

        async def handler(ctx, state):
            pass

        await proactive.continue_conversation(
            adapter, conv, handler, continuation_activity=custom_activity
        )
        assert captured_continuation is custom_activity

    @pytest.mark.asyncio
    async def test_continue_calls_adapter_with_correct_claims(self, proactive):
        conv = _make_conversation("claims-check")
        captured_claims = None

        async def fake_continue(claims, continuation, callback):
            nonlocal captured_claims
            captured_claims = claims
            state = _make_mock_state()
            ctx = MagicMock()
            with patch.object(proactive, "_load_state", AsyncMock(return_value=state)):
                await callback(ctx)

        adapter = MagicMock()
        adapter.continue_conversation_with_claims = AsyncMock(side_effect=fake_continue)

        async def handler(ctx, state):
            pass

        await proactive.continue_conversation(adapter, conv, handler)
        assert captured_claims is not None
        assert captured_claims.claims.get("aud") == "app-id"

    @pytest.mark.asyncio
    async def test_continue_propagates_exception_from_handler(self, proactive):
        conv = _make_conversation("exc-handler")

        async def bad_handler(ctx, state):
            raise ValueError("handler error")

        adapter, _ = self._make_adapter(proactive)
        with pytest.raises(ValueError, match="handler error"):
            await proactive.continue_conversation(adapter, conv, bad_handler)


# ---------------------------------------------------------------------------
# Create conversation
# ---------------------------------------------------------------------------


class TestProactiveCreateConversation:
    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def proactive(self, storage):
        return Proactive(_make_app(storage=storage), ProactiveOptions())

    @pytest.fixture
    def identity(self):
        return ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)

    @pytest.fixture
    def options(self, identity):
        return CreateConversationOptions(
            identity=identity,
            channel_id="msteams",
            parameters=ConversationParameters(),
            service_url="https://smba.trafficmanager.net/teams/",
        )

    def _make_adapter(self, new_conversation_id="new-conv"):
        ref = _make_reference(new_conversation_id)

        async def fake_create(
            app_id, channel_id, service_url, audience, params, callback
        ):
            ctx = MagicMock()
            ctx.activity.get_conversation_reference.return_value = ref
            await callback(ctx)

        adapter = MagicMock()
        adapter.create_conversation = AsyncMock(side_effect=fake_create)
        return adapter

    @pytest.mark.asyncio
    async def test_create_returns_conversation(self, proactive, options):
        adapter = self._make_adapter("new-conv-1")
        result = await proactive.create_conversation(adapter, options)
        assert result is not None
        assert isinstance(result, Conversation)

    @pytest.mark.asyncio
    async def test_create_sets_conversation_id(self, proactive, options):
        adapter = self._make_adapter("created-id")
        result = await proactive.create_conversation(adapter, options)
        assert result.conversation_reference.conversation.id == "created-id"

    @pytest.mark.asyncio
    async def test_create_sets_identity_on_result(self, proactive, options, identity):
        adapter = self._make_adapter("id-check")
        result = await proactive.create_conversation(adapter, options)
        assert result.claims.get("aud") == "app-id"

    @pytest.mark.asyncio
    async def test_create_calls_adapter_create_conversation(self, proactive, options):
        adapter = self._make_adapter("adapter-called")
        await proactive.create_conversation(adapter, options)
        adapter.create_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_validates_options(self, proactive):
        adapter = MagicMock()
        with pytest.raises(ValueError):
            await proactive.create_conversation(adapter, CreateConversationOptions())

    @pytest.mark.asyncio
    async def test_create_stores_conversation_when_flag_set(self, proactive, identity):
        opts = CreateConversationOptions(
            identity=identity,
            channel_id="msteams",
            parameters=ConversationParameters(),
            service_url="https://smba.trafficmanager.net/teams/",
            store_conversation=True,
        )
        adapter = self._make_adapter("auto-stored")
        await proactive.create_conversation(adapter, opts)
        stored = await proactive.get_conversation("auto-stored")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_does_not_store_by_default(self, proactive, options):
        adapter = self._make_adapter("not-stored")
        await proactive.create_conversation(adapter, options)
        stored = await proactive.get_conversation("not-stored")
        assert stored is None

    @pytest.mark.asyncio
    async def test_create_invokes_handler(self, proactive, options):
        handler_called = False

        async def handler(ctx, state):
            nonlocal handler_called
            handler_called = True

        state = _make_mock_state()
        adapter = self._make_adapter("handler-conv")

        with patch.object(proactive, "_load_state", AsyncMock(return_value=state)):
            await proactive.create_conversation(adapter, options, handler=handler)

        assert handler_called

    @pytest.mark.asyncio
    async def test_create_without_handler_does_not_raise(self, proactive, options):
        adapter = self._make_adapter("no-handler")
        result = await proactive.create_conversation(adapter, options, handler=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_passes_channel_id_to_adapter(self, proactive, options):
        captured_channel_id = None

        async def fake_create(
            app_id, channel_id, service_url, audience, params, callback
        ):
            nonlocal captured_channel_id
            captured_channel_id = channel_id
            ref = _make_reference("x")
            ctx = MagicMock()
            ctx.activity.get_conversation_reference.return_value = ref
            await callback(ctx)

        adapter = MagicMock()
        adapter.create_conversation = AsyncMock(side_effect=fake_create)

        await proactive.create_conversation(adapter, options)
        assert captured_channel_id == "msteams"

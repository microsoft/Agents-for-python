import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
)
from microsoft_agents.hosting.core.app.state import (
    ConversationState,
    TempState,
    TurnState,
)
from microsoft_agents.hosting.core.state.agent_state import CachedAgentState
from microsoft_agents.hosting.core.state import UserState
from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.turn_context import TurnContext

from tests._common.testing_objects import MockTestingAdapter


def _create_context():
    activity = Activity(
        type=ActivityTypes.message,
        channel_id="test-channel",
        conversation=ConversationAccount(id="conversation-123"),
        from_property=ChannelAccount(id="user-123"),
    )
    return TurnContext(MockTestingAdapter(), activity)


def test_turn_state_always_has_temp_scope():
    turn_state = TurnState()

    assert isinstance(turn_state.temp, TempState)
    assert turn_state.get_scope_by_name("temp") is turn_state.temp


def test_turn_state_with_storage_adds_default_persistent_scopes():
    storage = MemoryStorage()

    turn_state = TurnState.with_storage(storage)

    assert isinstance(turn_state.conversation, ConversationState)
    assert isinstance(turn_state.user, UserState)
    assert isinstance(turn_state.temp, TempState)


def test_turn_state_add_returns_self_and_registers_scope():
    storage = MemoryStorage()
    conversation_state = ConversationState(storage)
    turn_state = TurnState()

    result = turn_state.add(conversation_state)

    assert result is turn_state
    assert turn_state.get_scope(ConversationState) is conversation_state


def test_turn_state_add_rejects_none():
    turn_state = TurnState()

    with pytest.raises(ValueError, match="agent_state cannot be None"):
        turn_state.add(None)


def test_turn_state_get_scope_errors_for_missing_scope():
    turn_state = TurnState()

    with pytest.raises(ValueError, match="ConversationState"):
        turn_state.get_scope(ConversationState)

    with pytest.raises(ValueError, match="missing"):
        turn_state.get_scope_by_name("missing")


def test_turn_state_path_operations_default_to_temp_scope():
    turn_state = TurnState()

    assert not turn_state.has_value("name")

    turn_state.set_value("name", "value")

    assert turn_state.has_value("name")
    assert turn_state.get_value("name") == "value"

    turn_state.delete_value("name")

    assert not turn_state.has_value("name")


def test_turn_state_path_operations_use_named_scope():
    turn_state = TurnState()

    turn_state.set_value("temp.name", "value")

    assert turn_state.has_value("temp.name")
    assert turn_state.get_value("temp.name") == "value"


def test_turn_state_get_value_uses_default_factory_for_temp_scope():
    turn_state = TurnState()

    value = turn_state.get_value("items", lambda: [])
    value.append("item")

    assert turn_state.get_value("items") == ["item"]


def test_turn_state_clear_specific_scope_or_all_scopes():
    turn_state = TurnState()
    turn_state.set_value("temp.name", "value")

    turn_state.clear(None, scope="temp")

    assert not turn_state.has_value("temp.name")

    turn_state.set_value("temp.name", "value")
    turn_state.clear(None)

    assert not turn_state.has_value("temp.name")


@pytest.mark.asyncio
async def test_turn_state_load_initializes_default_scopes_with_storage():
    storage = MemoryStorage()
    context = _create_context()
    turn_state = TurnState()

    await turn_state.load(context, storage)

    assert isinstance(turn_state.conversation, ConversationState)
    assert isinstance(turn_state.user, UserState)
    assert isinstance(turn_state.temp, TempState)
    assert turn_state.conversation.get_cached_state(context) is not None
    assert turn_state.user.get_cached_state(context) is not None


@pytest.mark.asyncio
async def test_turn_state_save_persists_loaded_default_scopes():
    storage = MemoryStorage()
    context = _create_context()
    turn_state = TurnState()

    await turn_state.load(context, storage)
    turn_state.conversation.set_value("topic", {"value": "state"})
    await turn_state.save(context, force=True)

    storage_key = turn_state.conversation.get_storage_key(context)
    stored_items = await storage.read(
        [storage_key],
        target_cls=CachedAgentState,
    )
    conversation_cache = stored_items[storage_key]
    assert conversation_cache.state["topic"] == {"value": "state"}


def test_turn_state_scope_path_parser():
    assert TurnState._get_scope_and_path("name") == ("temp", "name")
    assert TurnState._get_scope_and_path("scope.name") == ("scope", "name")
    assert TurnState._get_scope_and_path("scope.nested.name") == (
        "scope",
        "nested.name",
    )

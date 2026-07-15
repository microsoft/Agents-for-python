import pytest
from types import SimpleNamespace

from microsoft_agents.activity import Activity, ActivityTypes, ConversationAccount
from microsoft_agents.hosting.core.app.state import ConversationState
from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.turn_context import TurnContext

from tests._common.testing_objects import MockTestingAdapter


def _create_context(channel_id="test-channel", conversation_id="conversation-123"):
    activity = Activity(
        type=ActivityTypes.message,
        channel_id=channel_id,
        conversation=ConversationAccount(id=conversation_id),
    )
    return TurnContext(MockTestingAdapter(), activity)


def test_conversation_state_uses_expected_context_service_key():
    state = ConversationState(MemoryStorage())

    assert state.CONTEXT_SERVICE_KEY == "ConversationState"


def test_get_storage_key_uses_channel_and_conversation_id():
    state = ConversationState(MemoryStorage())
    context = _create_context(
        channel_id="msteams",
        conversation_id="conversation-456",
    )

    assert state.get_storage_key(context) == "msteams/conversations/conversation-456"


def test_get_storage_key_raises_when_channel_id_is_missing():
    state = ConversationState(MemoryStorage())
    context = SimpleNamespace(
        activity=SimpleNamespace(
            channel_id="",
            conversation=SimpleNamespace(id="conversation-123"),
        )
    )

    with pytest.raises(ValueError, match="missing channel_id"):
        state.get_storage_key(context)


def test_get_storage_key_raises_when_conversation_id_is_missing():
    state = ConversationState(MemoryStorage())
    context = SimpleNamespace(
        activity=SimpleNamespace(
            channel_id="test-channel",
            conversation=SimpleNamespace(id=""),
        )
    )

    with pytest.raises(ValueError, match="missing conversation_id"):
        state.get_storage_key(context)


@pytest.mark.asyncio
async def test_clear_marks_conversation_state_changed():
    state = ConversationState(MemoryStorage())
    context = _create_context()

    await state.load(context)
    state.clear(context)

    cached_state = state._cached_state
    assert cached_state.state == {}
    assert cached_state.is_changed

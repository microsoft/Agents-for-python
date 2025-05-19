"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft.agents.builder.state.agent_state import AgentState, CachedAgentState
from microsoft.agents.builder.state.state_property_accessor import StatePropertyAccessor
from microsoft.agents.builder.turn_context import TurnContext
from microsoft.agents.storage import Storage, StoreItem

from .tools.testing_utility import TestingUtility
from .tools.testing_adapter import TestingAdapter


class MockStoreItem(StoreItem):
    def __init__(self, data=None):
        self.data = data or {}

    def store_item_to_json(self):
        return self.data

    @staticmethod
    def from_json_to_store_item(json_data):
        return MockStoreItem(json_data)


class TestPocoState(StoreItem):
    """Test POCO (Plain Old Class Object) state class."""

    def __init__(self, value=None):
        self.value = value

    def store_item_to_json(self):
        return {"value": self.value}

    @staticmethod
    def from_json_to_store_item(json_data):
        return TestPocoState(json_data.get("value"))


class TestState(StoreItem):
    """Test implementation of StoreItem for testing state persistence."""

    def __init__(self, value=None):
        self.value = value

    def store_item_to_json(self):
        return {"value": self.value}

    @staticmethod
    def from_json_to_store_item(json_data):
        return TestState(json_data.get("value"))


class TempState(AgentState):
    """Temporary state implementation for testing."""

    def __init__(self, storage: Storage = None):
        super().__init__(storage or MagicMock(spec=Storage), "TempState")

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        return "temp-state"


class UserState(AgentState):
    """User state implementation for testing."""

    def __init__(self, storage: Storage = None):
        super().__init__(storage or MagicMock(spec=Storage), "UserState")

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        if not turn_context.activity.from_property:
            raise ValueError("Activity.From or From.Id is null.")
        return f"{turn_context.activity.channel_id}/users/{turn_context.activity.from_property.id}"


class ConversationState(AgentState):
    """Conversation state implementation for testing."""

    def __init__(self, storage: Storage = None):
        super().__init__(storage or MagicMock(spec=Storage), "ConversationState")

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        if not turn_context.activity.conversation:
            raise ValueError("Activity.Conversation or Conversation.Id is null.")
        return f"{turn_context.activity.channel_id}/conversations/{turn_context.activity.conversation.id}"


class PrivateConversationState(AgentState):
    """Private conversation state implementation for testing."""

    def __init__(self, storage: Storage = None):
        super().__init__(storage or MagicMock(spec=Storage), "PrivateConversationState")

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        if not turn_context.activity.conversation:
            raise ValueError("Activity.Conversation or Conversation.Id is null.")
        if not turn_context.activity.from_property:
            raise ValueError("Activity.From or From.Id is null.")
        return f"{turn_context.activity.channel_id}/conversations/{turn_context.activity.conversation.id}/users/{turn_context.activity.from_property.id}"


class TestAgentState(AgentState):
    """Test implementation of AgentState for testing."""

    def __init__(self, storage: Storage = None, context_key: str = "test"):
        super().__init__(storage, context_key)

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        return f"test-agent-state:{turn_context.activity.conversation.id}"


class TestCustomKeyState(AgentState):
    """Test implementation of AgentState with custom storage key."""

    PROPERTY_NAME = "Microsoft.Agents.Builder.Tests.CustomKeyState"

    def __init__(self, storage: Storage = None):
        super().__init__(storage or MagicMock(spec=Storage), self.PROPERTY_NAME)

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        return "CustomKey"


class TestCachedAgentState:
    """Tests for the CachedAgentState class."""

    def test_initialization_with_empty_state(self):
        """Test initialization with empty state."""
        cached_state = CachedAgentState()
        assert cached_state.state == {}
        assert isinstance(cached_state.hash, int)
        assert not cached_state.has_state

    def test_initialization_with_state(self):
        """Test initialization with state data."""
        state_data = {"key": "value"}
        cached_state = CachedAgentState(state_data)
        assert cached_state.state == state_data
        assert isinstance(cached_state.hash, int)
        assert cached_state.has_state

    def test_is_changed(self):
        """Test is_changed property."""
        cached_state = CachedAgentState({"key": "value"})
        initial_hash = cached_state.hash

        # No change, should not be marked as changed
        assert not cached_state.is_changed

        # Modify state
        cached_state.state["key"] = "new_value"

        # Should be marked as changed
        assert cached_state.is_changed

        # Hash should still be the initial hash until compute_hash is called
        assert cached_state.hash == initial_hash

        # Update hash
        new_hash = cached_state.compute_hash()
        assert new_hash != initial_hash

        # Set the new hash
        cached_state.hash = new_hash

        # Should no longer be marked as changed
        assert not cached_state.is_changed

    def test_store_item_to_json(self):
        """Test converting to JSON."""
        # Test with regular values
        cached_state = CachedAgentState({"key": "value", "number": 42})
        json_data = cached_state.store_item_to_json()
        assert "key" in json_data
        assert json_data["key"] == "value"
        assert "number" in json_data
        assert json_data["number"] == 42

        # Test with nested StoreItem
        nested_item = MockStoreItem({"nested": "data"})
        cached_state = CachedAgentState({"item": nested_item})
        json_data = cached_state.store_item_to_json()
        assert "item" in json_data
        assert json_data["item"] == {"nested": "data"}

    def test_from_json_to_store_item(self):
        """Test creating from JSON."""
        json_data = {
            "key": "value",
            "number": 42,
        }
        cached_state = CachedAgentState.from_json_to_store_item(json_data)
        assert cached_state.state["key"] == "value"
        assert cached_state.state["number"] == 42
        assert cached_state.hash


class TestAgentStateClass:
    """Tests for the AgentState class."""

    def test_initialization(self):
        """Test initialization."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage, "test-context")

        assert agent_state._storage == storage
        assert agent_state._context_service_key == "test-context"

    def test_get_cached_state(self):
        """Test getting cached state."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context
        turn_context = MagicMock(spec=TurnContext)

        # First call should create a new cached state
        cached_state = agent_state.get_cached_state(turn_context)
        assert isinstance(cached_state, CachedAgentState)
        assert not cached_state.has_state

        # Should store the cached state in the turn context
        turn_context.turn_state.__setitem__.assert_called_once()

        # Reset mock
        turn_context.reset_mock()

        # Second call should return the same cached state
        turn_context.turn_state.__getitem__.return_value = cached_state
        second_cached_state = agent_state.get_cached_state(turn_context)
        assert second_cached_state is cached_state
        turn_context.turn_state.__setitem__.assert_not_called()

    def test_create_property(self):
        """Test creating a property accessor."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        accessor = agent_state.create_property("test_property")
        assert isinstance(accessor, StatePropertyAccessor)
        assert accessor._name == "test_property"

    @pytest.mark.asyncio
    async def test_get(self):
        """Test getting state data."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)
        test_value = MockStoreItem({"key2": "value"})
        cached_state = CachedAgentState({"key": test_value})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            state_data = agent_state.get(turn_context)

            assert (
                CachedAgentState(state_data).store_item_to_json()
                == cached_state.store_item_to_json()
            )

    @pytest.mark.asyncio
    async def test_load(self):
        """Test loading state."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity.conversation.id = "test-conversation"

        cached_state = CachedAgentState()

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Mock storage read to return some data
            storage_data = {
                "test-agent-state:test-conversation": {
                    "prop1": "value1",
                    "prop2": "value2",
                }
            }
            storage.read = AsyncMock(return_value=storage_data)

            # Load state
            await agent_state.load(turn_context)

            # Should have read from storage
            storage.read.assert_called_once_with(
                ["test-agent-state:test-conversation"], target_cls=CachedAgentState
            )

            # State should be populated with storage data
            assert cached_state.state == {
                "prop1": "value1",
                "prop2": "value2",
            }

    @pytest.mark.asyncio
    async def test_load_with_force(self):
        """Test loading state with force flag."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity.conversation.id = "test-conversation"

        # Create a cached state that already has data
        cached_state = CachedAgentState({"existing": "data"})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Mock storage read to return some data
            storage_data = {
                "test-agent-state:test-conversation": {
                    "prop1": "value1",
                    "prop2": "value2",
                }
            }
            storage.read = AsyncMock(return_value=storage_data)

            # Load state without force - should not read from storage
            await agent_state.load(turn_context)
            storage.read.assert_not_called()

            # Load state with force - should read from storage
            await agent_state.load(turn_context, force=True)
            storage.read.assert_called_once_with(
                ["test-agent-state:test-conversation"], target_cls=CachedAgentState
            )

            # State should be populated with storage data
            assert cached_state.state == {
                "prop1": "value1",
                "prop2": "value2",
            }

    @pytest.mark.asyncio
    async def test_save_changes(self):
        """Test saving state changes."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity.conversation.id = "test-conversation"

        # Create a cached state with data and mark as changed
        cached_state = CachedAgentState({"prop": "value"})
        original_hash = cached_state.hash
        cached_state.state["prop"] = (
            "new_value"  # Change to make is_changed return True
        )

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Mock storage write
            storage.write = AsyncMock()

            # Save changes
            await agent_state.save_changes(turn_context)

            # Should have written to storage
            storage.write.assert_called_once()

            # The hash should be updated
            assert cached_state.hash != original_hash

    @pytest.mark.asyncio
    async def test_save_no_changes(self):
        """Test saving when there are no changes."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)

        # Create a cached state with data but not changed
        cached_state = CachedAgentState({"prop": "value"})
        cached_state.hash = cached_state.compute_hash()  # Ensure hash is up to date

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Mock storage write
            storage.write = AsyncMock()

            # Save changes
            await agent_state.save_changes(turn_context)

            # Should not have written to storage
            storage.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_state(self):
        """Test clearing state."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity.conversation.id = "test-conversation"

        # Create a cached state with data
        cached_state = CachedAgentState({"prop": "value"})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):

            # Clear state
            await agent_state.clear_state(turn_context)

            # State should be empty
            assert turn_context
            assert not cached_state.has_state
            assert cached_state.state == {}

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting state."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity.conversation.id = "test-conversation"

        # Mock storage delete
        storage.delete = AsyncMock()

        # Delete state
        await agent_state.delete(turn_context)

        # Should have deleted from storage
        storage.delete.assert_called_once_with(["test-agent-state:test-conversation"])

    @pytest.mark.asyncio
    async def test_get_property_value(self):
        """Test getting a property value."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)

        # Create a cached state with data
        cached_state = CachedAgentState(
            {
                "string_prop": "string_value",
                "store_item_prop": MockStoreItem({"nested": "data"}),
            }
        )

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Get string property
            string_value = await agent_state.get_property_value(
                turn_context, "string_prop"
            )
            assert string_value == "string_value"

            # Get store item property
            store_item = await agent_state.get_property_value(
                turn_context, "store_item_prop", target_cls=MockStoreItem
            )
            assert isinstance(store_item, MockStoreItem)
            assert store_item.data == {"nested": "data"}

            # Get non-existent property
            none_value = await agent_state.get_property_value(
                turn_context, "non_existent"
            )
            assert none_value is None

    @pytest.mark.asyncio
    async def test_delete_property_value(self):
        """Test deleting a property value."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)

        # Create a cached state with data
        cached_state = CachedAgentState({"prop": "value"})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Delete property
            await agent_state.delete_property_value(turn_context, "prop")

            # Property should be deleted
            assert "prop" not in cached_state.state

    @pytest.mark.asyncio
    async def test_set_property_value(self):
        """Test setting a property value."""
        storage = MagicMock(spec=Storage)
        agent_state = TestAgentState(storage)

        # Create a mock turn context and cached state
        turn_context = MagicMock(spec=TurnContext)

        # Create a cached state
        cached_state = CachedAgentState({})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            # Set property
            await agent_state.set_property_value(turn_context, "prop", "value")

            # Property should be set
            assert cached_state.state["prop"] == "value"

    @pytest.mark.asyncio
    async def test_state_empty_name(self):
        """Test that empty property name raises an exception."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        with pytest.raises(TypeError):
            user_state.create_property("")

    @pytest.mark.asyncio
    async def test_state_null_name(self):
        """Test that null property name raises an exception."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        with pytest.raises(TypeError):
            user_state.create_property(None)

    @pytest.mark.asyncio
    async def test_load_set_save(self):
        """Test load-set-save cycle of state."""
        # Setup dictionary storage
        dictionary = {}
        storage = MagicMock(spec=Storage)
        storage.read = AsyncMock(return_value={})
        storage.write = AsyncMock(
            side_effect=lambda changes: dictionary.update(changes)
        )

        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        # Patch get_storage_key to return a predictable key
        with patch.object(user_state, "get_storage_key", return_value="test-key"):
            # Load state (empty)
            await user_state.load(context)

            # Set some properties
            await user_state.set_property_value(context, "property-a", "hello")
            await user_state.set_property_value(context, "property-b", "world")

            # Save changes
            await user_state.save_changes(context)

            # Check if storage.write was called with the correct data
            storage.write.assert_called_once()
            assert "test-key" in dictionary

    @pytest.mark.asyncio
    async def test_make_sure_storage_not_called_no_changes(self):
        """Test that storage is not called if there are no changes."""
        # Mock storage
        store_count = 0
        read_count = 0

        storage = MagicMock(spec=Storage)
        storage.read = AsyncMock(return_value={})
        storage.read.side_effect = (
            lambda *args, **kwargs: (read_count := read_count + 1) and {}
        )

        storage.write = AsyncMock()
        storage.write.side_effect = (
            lambda *args, **kwargs: (store_count := store_count + 1) or None
        )

        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        # Initial load
        await user_state.load(context, False)

        # No changes yet, save should not call storage
        assert store_count == 0
        await user_state.save_changes(context)
        assert store_count == 0

        # Set a property, should trigger read but not write
        await user_state.set_property_value(context, "propertyA", "hello")
        assert read_count == 1
        assert store_count == 0

        # Change property value
        await user_state.set_property_value(context, "propertyA", "there")
        assert store_count == 0  # No write yet

        # Explicit save should trigger write
        await user_state.save_changes(context)
        assert store_count == 1

        # Get value should not trigger write
        property_value = await user_state.get_property_value(context, "propertyA")
        assert property_value == "there"
        assert store_count == 1  # No change

        # Another save without changes should not trigger write
        await user_state.save_changes(context)
        assert store_count == 1  # No change

        # Delete property and save should trigger write
        await user_state.delete_property_value(context, "propertyA")
        assert store_count == 1  # No write yet
        await user_state.save_changes(context)
        assert store_count == 2  # Write happened

    @pytest.mark.asyncio
    async def test_state_with_default_values(self):
        """Test different state types with default values."""
        storage = MagicMock(spec=Storage)
        storage.read = AsyncMock(return_value={})
        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        # Load state (empty)
        await user_state.load(context, False)

        # Create property accessors
        poco_accessor = user_state.create_property("test-poco")
        bool_accessor = user_state.create_property("test-bool")
        int_accessor = user_state.create_property("test-int")

        # Test POCO with default factory
        poco_value = await poco_accessor.get(context, lambda: TestPocoState("default"))
        assert isinstance(poco_value, TestPocoState)
        assert poco_value.value == "default"

        # Test bool with default value
        bool_value = await bool_accessor.get(context, False)
        assert bool_value is False

        # Test int with default value
        int_value = await int_accessor.get(context, 42)
        assert int_value == 42

    @pytest.mark.asyncio
    async def test_conversation_bad_conversation_throws(self):
        """Test that ConversationState throws when conversation is null."""
        storage = MagicMock(spec=Storage)
        conversation_state = ConversationState(storage)
        context = TestingUtility.create_empty_context()

        # Set conversation to None
        context.activity.conversation = None

        # Should raise ValueError
        with pytest.raises(ValueError):
            await conversation_state.load(context, False)

    @pytest.mark.asyncio
    async def test_user_state_bad_from_throws(self):
        """Test that UserState throws when from is null."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)
        context = TestingUtility.create_empty_context()

        # Set from to None
        context.activity.from_property = None

        # Should raise ValueError
        with pytest.raises(ValueError):
            await user_state.load(context, False)

    @pytest.mark.asyncio
    async def test_private_conversation_state_bad_both_throws(self):
        """Test that PrivateConversationState throws when both from and conversation are null."""
        storage = MagicMock(spec=Storage)
        private_state = PrivateConversationState(storage)
        context = TestingUtility.create_empty_context()

        # Set both to None
        context.activity.conversation = None
        context.activity.from_property = None

        # Should raise ValueError
        with pytest.raises(ValueError):
            await private_state.load(context, False)

    @pytest.mark.asyncio
    async def test_clear_and_save(self):
        """Test clearing state and saving the changes."""
        storage = MagicMock(spec=Storage)
        state_dict = {}

        storage.read = AsyncMock(
            side_effect=lambda keys, **kwargs: {k: state_dict.get(k, {}) for k in keys}
        )
        storage.write = AsyncMock(
            side_effect=lambda changes: state_dict.update(changes)
        )

        # Create context
        context = TestingUtility.create_empty_context()
        context.activity.conversation.id = "1234"

        # Create a predictable storage key
        storage_key = "test-state-key"

        # Turn 0: Set initial value
        conversation_state1 = ConversationState(storage)
        with patch.object(
            conversation_state1, "get_storage_key", return_value=storage_key
        ):
            await conversation_state1.load(context, False)

            # Create property and set value
            property_accessor = conversation_state1.create_property("test-name")
            await property_accessor.set(context, TestPocoState("test-value"))

            # Save changes
            await conversation_state1.save_changes(context)

        # Turn 1: Verify value was saved
        conversation_state2 = ConversationState(storage)
        with patch.object(
            conversation_state2, "get_storage_key", return_value=storage_key
        ):
            await conversation_state2.load(context, False)

            # Get the property again
            property_accessor = conversation_state2.create_property("test-name")
            value1 = await property_accessor.get(context)

            # Verify the value is preserved
            assert isinstance(value1, TestPocoState)
            assert value1.value == "test-value"

        # Turn 2: Clear state
        conversation_state3 = ConversationState(storage)
        with patch.object(
            conversation_state3, "get_storage_key", return_value=storage_key
        ):
            await conversation_state3.load(context, False)

            # Clear the state
            await conversation_state3.clear_state(context)

            # Save changes
            await conversation_state3.save_changes(context)

        # Turn 3: Verify state was cleared
        conversation_state4 = ConversationState(storage)
        with patch.object(
            conversation_state4, "get_storage_key", return_value=storage_key
        ):
            await conversation_state4.load(context, False)

            # Get the property with default value
            property_accessor = conversation_state4.create_property("test-name")
            value2 = await property_accessor.get(
                context, lambda: TestPocoState("default-value")
            )

            # Should have the default value
            assert value2.value == "default-value"

    @pytest.mark.asyncio
    async def test_state_delete(self):
        """Test deleting state."""
        storage = MagicMock(spec=Storage)
        state_dict = {}

        storage.read = AsyncMock(
            side_effect=lambda keys, **kwargs: {k: state_dict.get(k, {}) for k in keys}
        )
        storage.write = AsyncMock(
            side_effect=lambda changes: state_dict.update(changes)
        )
        storage.delete = AsyncMock(
            side_effect=lambda keys: [state_dict.pop(k, None) for k in keys]
        )

        # Create context
        context = TestingUtility.create_empty_context()
        context.activity.conversation.id = "1234"

        # Create a predictable storage key
        storage_key = "test-state-key"

        # Turn 0: Set initial value
        conversation_state1 = ConversationState(storage)
        with patch.object(
            conversation_state1, "get_storage_key", return_value=storage_key
        ):
            await conversation_state1.load(context, False)

            # Create property and set value
            property_accessor = conversation_state1.create_property("test-name")
            await property_accessor.set(context, TestPocoState("test-value"))

            # Save changes
            await conversation_state1.save_changes(context)

        # Turn 1: Verify value was saved
        conversation_state2 = ConversationState(storage)
        with patch.object(
            conversation_state2, "get_storage_key", return_value=storage_key
        ):
            await conversation_state2.load(context, False)

            # Get the property again
            property_accessor = conversation_state2.create_property("test-name")
            value1 = await property_accessor.get(context)

            # Verify the value is preserved
            assert isinstance(value1, TestPocoState)
            assert value1.value == "test-value"

        # Turn 2: Delete state
        conversation_state3 = ConversationState(storage)
        with patch.object(
            conversation_state3, "get_storage_key", return_value=storage_key
        ):
            # Delete state
            await conversation_state3.delete(context)

            # Verify delete was called
            storage.delete.assert_called_once_with([storage_key])

        # Turn 3: Verify state was deleted
        conversation_state4 = ConversationState(storage)
        with patch.object(
            conversation_state4, "get_storage_key", return_value=storage_key
        ):
            await conversation_state4.load(context, False)

            # Get the property with default value
            property_accessor = conversation_state4.create_property("test-name")
            value2 = await property_accessor.get(
                context, lambda: TestPocoState("default-value")
            )

            # Should have the default value
            assert value2.value == "default-value"

    @pytest.mark.asyncio
    async def test_custom_key_state(self):
        """Test state with custom storage key."""
        # Setup the test adapter
        adapter = TestingAdapter()

        # Create a storage instance
        storage = MagicMock(spec=Storage)
        state_dict = {}
        test_guid = "test-unique-value"

        storage.read = AsyncMock(return_value={})
        storage.write = AsyncMock(
            side_effect=lambda changes: state_dict.update(changes)
        )

        # Create the custom key state
        custom_state = TestCustomKeyState(storage)

        # Test conversation
        async def test_activity_handler(turn_context):
            # Load the state for this turn
            await custom_state.load(turn_context, False)

            # Get the test property accessor
            test_accessor = custom_state.create_property("test")
            test_state = await test_accessor.get(turn_context, lambda: TestPocoState())

            if turn_context.activity.text == "set value":
                # Set the value
                test_state.value = test_guid
                # Save changes (normally would be done by middleware)
                await custom_state.save_changes(turn_context)
                await turn_context.send_activity("value saved")
            elif turn_context.activity.text == "get value":
                # Return the saved value
                await turn_context.send_activity(test_state.value)

        # Send the "set value" message
        activities = await adapter.test("set value", test_activity_handler)
        assert len(activities) == 1
        assert activities[0].text == "value saved"

        # Send the "get value" message to verify it was saved correctly
        activities = await adapter.test("get value", test_activity_handler)
        assert len(activities) == 1
        assert activities[0].text == test_guid

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


class MockStoreItem(StoreItem):
    def __init__(self, data=None):
        self.data = data or {}

    def store_item_to_json(self):
        return self.data

    @staticmethod
    def from_json_to_store_item(json_data):
        return MockStoreItem(json_data)


class TestAgentState(AgentState):
    """Test implementation of AgentState for testing."""

    def __init__(self, storage: Storage = None, context_key: str = "test"):
        super().__init__(storage, context_key)

    def get_storage_key(self, turn_context: TurnContext, *, target_cls=None) -> str:
        return f"test-agent-state:{turn_context.activity.conversation.id}"


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
        assert "CachedAgentState._hash" in json_data
        assert json_data["CachedAgentState._hash"] == cached_state.hash

        # Test with nested StoreItem
        nested_item = MockStoreItem({"nested": "data"})
        cached_state = CachedAgentState({"item": nested_item})
        json_data = cached_state.store_item_to_json()
        assert "item" in json_data
        assert json_data["item"] == {"nested": "data"}

    def test_from_json_to_store_item(self):
        """Test creating from JSON."""
        json_data = {"key": "value", "number": 42, "CachedAgentState._hash": 12345}
        cached_state = CachedAgentState.from_json_to_store_item(json_data)
        assert cached_state.state["key"] == "value"
        assert cached_state.state["number"] == 42
        assert cached_state.hash == 12345


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
        cached_state = CachedAgentState({"key": "value"})

        # Make get_cached_state return our mock
        with patch.object(agent_state, "get_cached_state", return_value=cached_state):
            state_data = agent_state.get(turn_context)

            assert state_data == {"key": "value"}

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
                    "CachedAgentState._hash": 12345,
                }
            }
            storage.read = AsyncMock(return_value=storage_data)

            # Load state
            await agent_state.load(turn_context)

            # Should have read from storage
            storage.read.assert_called_once_with(["test-agent-state:test-conversation"])

            # State should be populated with storage data
            assert cached_state.state == {
                "prop1": "value1",
                "prop2": "value2",
                "CachedAgentState._hash": 12345,
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
                    "CachedAgentState._hash": 12345,
                }
            }
            storage.read = AsyncMock(return_value=storage_data)

            # Load state without force - should not read from storage
            await agent_state.load(turn_context)
            storage.read.assert_not_called()

            # Load state with force - should read from storage
            await agent_state.load(turn_context, force=True)
            storage.read.assert_called_once_with(["test-agent-state:test-conversation"])

            # State should be populated with storage data
            assert cached_state.state == {
                "prop1": "value1",
                "prop2": "value2",
                "CachedAgentState._hash": 12345,
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
            # Mock storage delete
            storage.delete = AsyncMock()

            # Clear state
            await agent_state.clear_state(turn_context)

            # Should have deleted from storage
            storage.delete.assert_called_once_with(
                ["test-agent-state:test-conversation"]
            )

            # State should be empty
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

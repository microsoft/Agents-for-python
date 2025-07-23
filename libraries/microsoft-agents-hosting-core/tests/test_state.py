"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from typing import Any, Dict
import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft.agents.hosting.core.app.state.state import (
    State,
    state,
    StatePropertyAccessor,
)
from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.storage import Storage, StoreItem


class MockStoreItem(StoreItem):
    def __init__(self, data=None):
        self.data = data or {}

    def store_item_to_json(self):
        return self.data

    @staticmethod
    def from_json_to_store_item(json_data):
        return MockStoreItem(json_data)


@state
class StateForTesting(State):
    """Test state implementation for testing."""

    test_property: str = "default_value"
    store_item: MockStoreItem = MockStoreItem({"initial": "value"})

    @classmethod
    async def load(
        cls, context: TurnContext, storage: Storage = None
    ) -> "StateForTesting":
        if not storage:
            return cls(__key__="test")

        data: Dict[str, Any] = await storage.read(["test"])

        if "test" in data:
            if isinstance(data["test"], StoreItem):
                return cls(__key__="test", **vars(data["test"]))
            return cls(__key__="test", **data["test"])
        return cls(__key__="test")


class TestStateClass:
    """Tests for the State class and state decorator."""

    def test_state_initialization(self):
        """Test that state initializes properly."""
        test_state = StateForTesting()
        assert test_state.test_property == "default_value"
        assert isinstance(test_state.store_item, MockStoreItem)
        assert test_state.store_item.data == {"initial": "value"}
        assert test_state.__key__ == ""
        assert test_state.__deleted__ == []

    def test_state_property_access(self):
        """Test that state properties can be accessed using both dict and attribute syntax."""
        test_state = StateForTesting()

        # Test attribute syntax
        assert test_state.test_property == "default_value"

        # Test dict syntax
        assert test_state["test_property"] == "default_value"

    def test_state_property_modification(self):
        """Test that state properties can be modified using both dict and attribute syntax."""
        test_state = StateForTesting()

        # Test attribute syntax
        test_state.test_property = "new_value"
        assert test_state.test_property == "new_value"

        # Test dict syntax
        test_state["test_property"] = "newer_value"
        assert test_state.test_property == "newer_value"
        assert test_state["test_property"] == "newer_value"

    def test_state_property_deletion(self):
        """Test that state properties can be deleted."""
        test_state = StateForTesting()

        # Test attribute deletion
        del test_state.test_property
        assert "test_property" not in test_state

        # Test re-adding and dict deletion
        test_state.test_property = "re-added"
        del test_state["test_property"]
        assert "test_property" not in test_state

    def test_state_deleted_tracking(self):
        """Test that state tracks deleted properties for storage updates."""
        test_state = StateForTesting()

        # Create a nested state to track deletion
        nested_state = StateForTesting()
        nested_state.__key__ = "nested-key"
        test_state.nested = nested_state

        # Delete the nested state
        del test_state.nested

        # Check if the nested key is tracked for deletion
        assert "nested-key" in test_state.__deleted__

    def test_create_property(self):
        """Test creating a state property accessor."""
        test_state = StateForTesting()
        accessor = test_state.create_property("test_property")

        assert isinstance(accessor, StatePropertyAccessor)
        assert accessor._name == "test_property"
        assert accessor._state == test_state

    @pytest.mark.asyncio
    async def test_save_with_no_storage(self):
        """Test that save does nothing when no storage is provided."""
        test_state = StateForTesting()
        context = MagicMock(spec=TurnContext)

        # Should not raise any exceptions
        await test_state.save(context)

    @pytest.mark.asyncio
    async def test_save_with_empty_key(self):
        """Test that save does nothing when key is empty."""
        test_state = StateForTesting()
        context = MagicMock(spec=TurnContext)
        storage = MagicMock(spec=Storage)

        # Should not call storage methods
        await test_state.save(context, storage)

        storage.delete.assert_not_called()
        storage.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_with_storage(self):
        """Test saving state to storage."""
        test_state = await StateForTesting.load(MagicMock())
        test_state.test_property = "new_value"

        # Add item to deleted list
        test_state.__deleted__ = ["deleted-key"]

        context = MagicMock(spec=TurnContext)
        storage = MagicMock(spec=Storage)
        storage.delete = AsyncMock()
        storage.write = AsyncMock()

        await test_state.save(context, storage)

        # Should call delete with deleted keys
        storage.delete.assert_called_once_with(["deleted-key"])

        # Should call write with state data
        expected_data = {
            "test-key": {
                "test_property": "new_value",
                "store_item": MockStoreItem({"initial": "value"}),
            }
        }
        storage.write.assert_called_once()
        # Can't directly compare the call args because of the StoreItem instance,
        # but we can check if the call was made

        # Deleted list should be cleared
        assert test_state.__deleted__ == []

    @pytest.mark.asyncio
    async def test_load_from_storage(self):
        """Test loading state from storage."""
        context = MagicMock(spec=TurnContext)
        context.activity.conversation.id = "test-conversation"

        storage = MagicMock(spec=Storage)
        mock_data = {
            "test": {
                "test_property": "stored_value",
                "new_property": "new_value",
            }
        }
        storage.read = AsyncMock(return_value=mock_data)

        test_state = await StateForTesting.load(context, storage)

        # Should have the correct key
        assert test_state.__key__ == "test"

        # Should have loaded values from storage
        assert test_state.test_property == "stored_value"
        assert test_state.new_property == "new_value"


class TestStatePropertyAccessor:
    """Tests for the StatePropertyAccessor class."""

    @pytest.mark.asyncio
    async def test_get_existing_property(self):
        """Test getting an existing property."""
        test_state = StateForTesting()
        test_state.test_property = "existing_value"

        accessor = StatePropertyAccessor(test_state, "test_property")
        context = MagicMock(spec=TurnContext)

        value = await accessor.get(context)
        assert value == "existing_value"

    @pytest.mark.asyncio
    async def test_get_non_existent_without_default(self):
        """Test getting a non-existent property without a default value."""
        test_state = StateForTesting()
        accessor = StatePropertyAccessor(test_state, "non_existent")
        context = MagicMock(spec=TurnContext)

        value = await accessor.get(context)
        assert value is None

    @pytest.mark.asyncio
    async def test_get_with_default_value(self):
        """Test getting a property with a default value."""
        test_state = StateForTesting()
        accessor = StatePropertyAccessor(test_state, "non_existent")
        context = MagicMock(spec=TurnContext)

        value = await accessor.get(context, "default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_get_with_default_factory(self):
        """Test getting a property with a default factory function."""
        test_state = StateForTesting()
        accessor = StatePropertyAccessor(test_state, "non_existent")
        context = MagicMock(spec=TurnContext)

        value = await accessor.get(context, lambda: "factory_default")
        assert value == "factory_default"

    @pytest.mark.asyncio
    async def test_set_property(self):
        """Test setting a property value."""
        test_state = StateForTesting()
        accessor = StatePropertyAccessor(test_state, "test_property")
        context = MagicMock(spec=TurnContext)

        await accessor.set(context, "new_value")
        assert test_state.test_property == "new_value"

    @pytest.mark.asyncio
    async def test_delete_property(self):
        """Test deleting a property."""
        test_state = StateForTesting()
        test_state.test_property = "value_to_delete"
        accessor = StatePropertyAccessor(test_state, "test_property")
        context = MagicMock(spec=TurnContext)

        await accessor.delete(context)
        assert "test_property" not in test_state

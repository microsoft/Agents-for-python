"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Test suite for the AgentState class that closely follows the C# test implementation.
"""

import asyncio
import pytest
from typing import Type
from unittest.mock import AsyncMock, MagicMock

from microsoft.agents.hosting.core.state.agent_state import (
    AgentState,
    CachedAgentState,
    BotStatePropertyAccessor,
)
from microsoft.agents.hosting.core.state.user_state import UserState
from microsoft.agents.hosting.core.app.state.conversation_state import ConversationState
from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.storage import Storage, StoreItem, MemoryStorage
from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
)
from tests.tools.testing_adapter import TestingAdapter


class MockCustomState(AgentState):
    """Custom state implementation for testing."""

    def __init__(self, storage: Storage, namespace: str = ""):
        self.namespace = namespace
        super().__init__(storage, "MockCustomState")

    def get_storage_key(
        self, turn_context: TurnContext, *, target_cls: Type[StoreItem] = None
    ) -> str:
        """
        Returns the storage key for the custom state.
        """
        conversation_id = turn_context.activity.conversation.id
        if not conversation_id:
            raise ValueError("Invalid activity: missing conversation.id")

        key = f"custom/{conversation_id}"
        if self.namespace:
            key = f"{self.namespace}/{key}"
        return key


class TestDataItem(StoreItem):
    """Test data item for testing state functionality."""

    def __init__(self, value: str = None):
        self.value = value or "default"

    def store_item_to_json(self) -> dict:
        return {"value": self.value}

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "TestDataItem":
        return TestDataItem(json_data.get("value", "default"))


class TestAgentState:
    """
    Comprehensive test suite for AgentState functionality.
    Tests various scenarios including property accessors, state management,
    storage operations, caching, and different state implementations.
    """

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.storage = MemoryStorage()
        self.user_state = UserState(self.storage)
        self.conversation_state = ConversationState(self.storage)
        self.custom_state = MockCustomState(self.storage)

        # Create a test context
        self.adapter = TestingAdapter()
        self.activity = Activity(
            type=ActivityTypes.message,
            channel_id="test-channel",
            conversation=ConversationAccount(id="test-conversation"),
            from_property=ChannelAccount(id="test-user"),
            text="test message",
        )
        self.context = TurnContext(self.adapter, self.activity)

    @pytest.mark.asyncio
    async def test_empty_property_name_throws_exception(self):
        """Test that creating property with empty name throws exception."""
        # Test empty string
        with pytest.raises(ValueError, match="cannot be None or empty"):
            self.user_state.create_property("")

        # Test None
        with pytest.raises(ValueError, match="cannot be None or empty"):
            self.user_state.create_property(None)

        # Test whitespace
        with pytest.raises(ValueError, match="cannot be None or empty"):
            self.user_state.create_property("   ")

    @pytest.mark.asyncio
    async def test_get_property_works(self):
        """Test getting property values."""
        property_name = "test_property"
        property_accessor = self.user_state.create_property(property_name)

        # Test getting non-existent property returns None
        value = await property_accessor.get(self.context)
        assert value is None

    @pytest.mark.asyncio
    async def test_get_property_with_default_value(self):
        """Test getting property with default value."""
        property_name = "test_property"
        default_value = "default_test_value"
        property_accessor = self.user_state.create_property(property_name)

        # Test getting with default value
        value = await property_accessor.get(self.context, default_value)
        assert value == default_value

    @pytest.mark.asyncio
    async def test_get_property_with_default_factory(self):
        """Test getting property with default factory function."""
        property_name = "test_property"
        default_factory = lambda: TestDataItem("factory_value")
        property_accessor = self.user_state.create_property(property_name)

        # Test getting with factory
        value = await property_accessor.get(self.context, default_factory)
        assert isinstance(value, TestDataItem)
        assert value.value == "factory_value"

    @pytest.mark.asyncio
    async def test_set_property_works(self):
        """Test setting property values."""
        property_name = "test_property"
        test_value = TestDataItem("test_value")
        property_accessor = self.user_state.create_property(property_name)

        # Set the property
        await property_accessor.set(self.context, test_value)

        # Verify it was set
        retrieved_value = await property_accessor.get(self.context)
        assert isinstance(retrieved_value, TestDataItem)
        assert retrieved_value.value == "test_value"

    @pytest.mark.asyncio
    async def test_delete_property_works(self):
        """Test deleting property values."""
        property_name = "test_property"
        test_value = TestDataItem("test_value")
        property_accessor = self.user_state.create_property(property_name)

        # Set then delete the property
        await property_accessor.set(self.context, test_value)
        await property_accessor.delete(self.context)

        # Verify it was deleted
        value = await property_accessor.get(self.context)
        assert value is None

    @pytest.mark.asyncio
    async def test_state_load_no_existing_state(self):
        """Test loading state when no existing state exists."""
        await self.user_state.load(self.context)

        # Should have cached state object
        cached_state = self.user_state.get_cached_state(self.context)
        assert cached_state is not None
        assert isinstance(cached_state, CachedAgentState)

    @pytest.mark.asyncio
    async def test_state_load_with_force(self):
        """Test loading state with force flag."""
        # Load once
        await self.user_state.load(self.context)
        cached_state_1 = self.user_state.get_cached_state(self.context)

        # Load again with force
        await self.user_state.load(self.context, force=True)
        cached_state_2 = self.user_state.get_cached_state(self.context)

        # Should have refreshed the cached state
        assert cached_state_1 is not cached_state_2

    @pytest.mark.asyncio
    async def test_state_save_no_changes(self):
        """Test saving changes when no changes exist."""
        await self.user_state.load(self.context)

        # Save without making changes - should not call storage
        storage_mock = MagicMock(spec=Storage)
        storage_mock.write = AsyncMock()
        self.user_state._storage = storage_mock

        await self.user_state.save(self.context)
        storage_mock.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_state_save_with_changes(self):
        """Test saving changes when changes exist."""
        await self.user_state.load(self.context)

        # Make a change
        property_accessor = self.user_state.create_property("test_property")
        await property_accessor.set(self.context, TestDataItem("changed_value"))

        # Save changes
        await self.user_state.save(self.context)

        # Verify the change was persisted by loading fresh state
        fresh_context = TurnContext(self.adapter, self.activity)
        await self.user_state.load(fresh_context)
        fresh_accessor = self.user_state.create_property("test_property")
        value = await fresh_accessor.get(fresh_context, target_cls=TestDataItem)

        assert isinstance(value, TestDataItem)
        assert value.value == "changed_value"

    @pytest.mark.asyncio
    async def test_state_save_with_force(self):
        """Test saving changes with force flag."""
        await self.user_state.load(self.context)

        # Use a mock storage to verify write is called even without changes
        storage_mock = MagicMock(spec=Storage)
        storage_mock.write = AsyncMock()
        self.user_state._storage = storage_mock

        await self.user_state.save(self.context, force=True)

        # Should call write even without changes when force=True
        storage_mock.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_state_instances(self):
        """Test that multiple state instances work independently."""
        # Create two different state instances
        user_state_1 = UserState(self.storage, "namespace1")
        user_state_2 = UserState(self.storage, "namespace2")

        # Load both states
        await user_state_1.load(self.context)
        await user_state_2.load(self.context)

        # Set different values in each
        prop_1 = user_state_1.create_property("test_prop")
        prop_2 = user_state_2.create_property("test_prop")

        await prop_1.set(self.context, TestDataItem("value1"))
        await prop_2.set(self.context, TestDataItem("value2"))

        # Verify they are independent
        val_1 = await prop_1.get(self.context)
        val_2 = await prop_2.get(self.context)

        assert val_1.value == "value1"
        assert val_2.value == "value2"

    @pytest.mark.asyncio
    async def test_state_persistence_across_contexts(self):
        """Test that state persists across different contexts."""
        # Set a value in first context
        property_accessor = self.user_state.create_property("persistent_prop")
        await self.user_state.load(self.context)
        await property_accessor.set(self.context, TestDataItem("persistent_value"))
        await self.user_state.save(self.context)

        # Create a new context with same user
        new_context = TurnContext(self.adapter, self.activity)
        new_user_state = UserState(self.storage)
        new_property_accessor = new_user_state.create_property("persistent_prop")

        # Load state in new context
        await new_user_state.load(new_context)
        value = await new_property_accessor.get(new_context, target_cls=TestDataItem)

        assert isinstance(value, TestDataItem)
        assert value.value == "persistent_value"

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing state."""
        # Set some values
        await self.user_state.load(self.context)
        prop_accessor = self.user_state.create_property("test_prop")
        await prop_accessor.set(self.context, TestDataItem("test_value"))

        # Clear state
        self.user_state.clear(self.context)
        await self.user_state.save(self.context)

        # Verify state is cleared
        value = await prop_accessor.get(self.context)
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_state(self):
        """Test deleting state from storage."""
        # Set and save a value
        await self.user_state.load(self.context)
        prop_accessor = self.user_state.create_property("test_prop")
        await prop_accessor.set(self.context, TestDataItem("test_value"))
        await self.user_state.save(self.context)

        # Delete state
        await self.user_state.delete(self.context)

        # Create new context and verify state is gone
        new_context = TurnContext(self.adapter, self.activity)
        new_user_state = UserState(self.storage)
        await new_user_state.load(new_context)
        new_prop_accessor = new_user_state.create_property("test_prop")
        value = await new_prop_accessor.get(new_context)

        assert value is None

    @pytest.mark.asyncio
    async def test_conversation_state_storage_key(self):
        """Test conversation state generates correct storage key."""
        storage_key = self.conversation_state.get_storage_key(self.context)
        expected_key = "test-channel/conversations/test-conversation"
        assert storage_key == expected_key

    @pytest.mark.asyncio
    async def test_user_state_storage_key(self):
        """Test user state generates correct storage key."""
        storage_key = self.user_state.get_storage_key(self.context)
        expected_key = "test-channel/users/test-user"
        assert storage_key == expected_key

    @pytest.mark.asyncio
    async def test_custom_state_implementation(self):
        """Test custom state implementation."""
        # Test custom state works like built-in states
        await self.custom_state.load(self.context)
        prop_accessor = self.custom_state.create_property("custom_prop")

        await prop_accessor.set(self.context, TestDataItem("custom_value"))
        await self.custom_state.save(self.context)

        # Verify storage key format
        storage_key = self.custom_state.get_storage_key(self.context)
        expected_key = "custom/test-conversation"
        assert storage_key == expected_key

    @pytest.mark.asyncio
    async def test_invalid_context_missing_channel_id(self):
        """Test error handling for invalid context missing channel ID."""
        invalid_activity = Activity(
            type=ActivityTypes.message,
            conversation=ConversationAccount(id="test-conversation"),
            from_property=ChannelAccount(id="test-user"),
            # Missing channel_id
        )
        invalid_context = TurnContext(self.adapter, invalid_activity)

        with pytest.raises((TypeError, ValueError)):
            self.user_state.get_storage_key(invalid_context)

    @pytest.mark.asyncio
    async def test_invalid_context_missing_user_id(self):
        """Test error handling for invalid context missing user ID."""
        invalid_activity = Activity(
            type=ActivityTypes.message,
            channel_id="test-channel",
            conversation=ConversationAccount(id="test-conversation"),
            # Missing from_property
        )
        invalid_context = TurnContext(self.adapter, invalid_activity)

        with pytest.raises((TypeError, ValueError, AttributeError)):
            self.user_state.get_storage_key(invalid_context)

    @pytest.mark.asyncio
    async def test_invalid_context_missing_conversation_id(self):
        """Test error handling for invalid context missing conversation ID."""
        invalid_activity = Activity(
            type=ActivityTypes.message,
            channel_id="test-channel",
            from_property=ChannelAccount(id="test-user"),
            # Missing conversation
        )
        invalid_context = TurnContext(self.adapter, invalid_activity)

        with pytest.raises((TypeError, ValueError, AttributeError)):
            self.conversation_state.get_storage_key(invalid_context)

    @pytest.mark.asyncio
    async def test_cached_state_hash_computation(self):
        """Test cached state hash computation and change detection."""
        await self.user_state.load(self.context)
        cached_state = self.user_state.get_cached_state(self.context)

        # Initial state should not be changed
        assert not cached_state.is_changed

        # Make a change
        prop_accessor = self.user_state.create_property("test_prop")
        await prop_accessor.set(self.context, TestDataItem("test_value"))

        # State should now be changed
        assert cached_state.is_changed

    @pytest.mark.asyncio
    async def test_concurrent_state_operations(self):
        """Test concurrent state operations."""
        # Create multiple accessors
        accessors = [self.user_state.create_property(f"prop_{i}") for i in range(5)]

        await self.user_state.load(self.context)

        # Set values concurrently
        await asyncio.gather(
            *[
                accessor.set(self.context, TestDataItem(f"value_{i}"))
                for i, accessor in enumerate(accessors)
            ]
        )

        # Verify all values were set correctly
        values = await asyncio.gather(
            *[accessor.get(self.context) for accessor in accessors]
        )

        for i, value in enumerate(values):
            assert isinstance(value, TestDataItem)
            assert value.value == f"value_{i}"

    @pytest.mark.asyncio
    async def test_state_isolation_between_different_state_types(self):
        """Test that different state types (User, Conversation) are isolated."""
        # Load both states
        await self.user_state.load(self.context)
        await self.conversation_state.load(self.context)

        # Set same property name in both
        user_prop = self.user_state.create_property("shared_prop")
        conv_prop = self.conversation_state.create_property("shared_prop")

        await user_prop.set(self.context, TestDataItem("user_value"))
        await conv_prop.set(self.context, TestDataItem("conversation_value"))

        # Verify they are isolated
        user_value = await user_prop.get(self.context)
        conv_value = await conv_prop.get(self.context)

        assert user_value.value == "user_value"
        assert conv_value.value == "conversation_value"

    @pytest.mark.asyncio
    async def test_storage_exceptions_handling(self):
        """Test handling of storage exceptions."""
        # Create a mock storage that throws exceptions
        failing_storage = MagicMock(spec=Storage)
        failing_storage.read = AsyncMock(side_effect=Exception("Storage read failed"))
        failing_storage.write = AsyncMock(side_effect=Exception("Storage write failed"))

        failing_user_state = UserState(failing_storage)

        # Load should handle storage exceptions gracefully
        with pytest.raises(Exception, match="Storage read failed"):
            await failing_user_state.load(self.context)

    def test_agent_state_context_service_key(self):
        """Test that AgentState has correct context service key."""
        assert self.user_state._context_service_key == "Internal.UserState"
        assert self.conversation_state._context_service_key == "ConversationState"

    @pytest.mark.asyncio
    async def test_memory_storage_integration(self):
        """Test AgentState integration with MemoryStorage."""
        memory_storage = MemoryStorage()
        user_state = UserState(memory_storage)

        # Test complete workflow
        await user_state.load(self.context)
        prop_accessor = user_state.create_property("memory_test")

        await prop_accessor.set(self.context, TestDataItem("memory_value"))
        await user_state.save(self.context)

        # Verify data exists in memory storage
        storage_key = user_state.get_storage_key(self.context)
        stored_data = await memory_storage.read([storage_key], target_cls=TestDataItem)

        assert storage_key in stored_data
        assert stored_data[storage_key] is not None

    @pytest.mark.asyncio
    async def test_state_property_accessor_error_conditions(self):
        """Test StatePropertyAccessor error conditions."""
        # Test with None state
        with pytest.raises(TypeError):
            BotStatePropertyAccessor(None, "test_prop")

        # Test with invalid property name types
        for invalid_name in [None, "", "   "]:
            if isinstance(invalid_name, str) and not invalid_name.strip():
                with pytest.raises(ValueError):
                    self.user_state.create_property(invalid_name)
            elif not isinstance(invalid_name, str):
                with pytest.raises((TypeError, ValueError)):
                    self.user_state.create_property(invalid_name)

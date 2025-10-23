# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import Mock, AsyncMock

from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.storage._wrappers._item_namespace import _ItemNamespace
from microsoft_agents.hosting.core.storage._wrappers._storage_namespace import _StorageNamespace
from tests._common.storage.utils import MockStoreItem, MockStoreItemB


class TestItemNamespace:
    """Test cases for the _ItemNamespace class."""

    def test_init_valid_params(self):
        """Test successful initialization with valid parameters."""
        storage = MemoryStorage()
        base_key = "test_namespace"
        item_cls = MockStoreItem
        
        item_namespace = _ItemNamespace(base_key, storage, item_cls)
        
        # Verify that it properly wraps the storage in a _StorageNamespace
        assert isinstance(item_namespace._storage, _StorageNamespace)
        assert item_namespace._storage.base_key == base_key
        assert item_namespace._item_cls is item_cls

    def test_init_with_different_item_types(self):
        """Test initialization with different StoreItem types."""
        storage = MemoryStorage()
        base_key = "test_namespace"
        
        # Test with MockStoreItem
        item_namespace_a = _ItemNamespace(base_key, storage, MockStoreItem)
        assert item_namespace_a._item_cls is MockStoreItem
        
        # Test with MockStoreItemB
        item_namespace_b = _ItemNamespace(base_key, storage, MockStoreItemB)
        assert item_namespace_b._item_cls is MockStoreItemB

    def test_init_with_different_base_keys(self):
        """Test initialization with different base key formats."""
        storage = MemoryStorage()
        
        test_base_keys = [
            "simple",
            "auth/channel123/user456",
            "oauth.handler.state",
            "nested:namespace:with:colons",
            "namespace_with_underscores",
            "namespace-with-dashes"
        ]
        
        for base_key in test_base_keys:
            item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
            assert item_namespace._storage.base_key == base_key

    def test_init_empty_base_key_raises_error(self):
        """Test that empty base_key raises ValueError."""
        storage = MemoryStorage()
        
        with pytest.raises(ValueError):
            _ItemNamespace("", storage, MockStoreItem)

    def test_init_none_base_key_raises_error(self):
        """Test that None base_key raises ValueError."""
        storage = MemoryStorage()
        
        with pytest.raises(ValueError):
            _ItemNamespace(None, storage, MockStoreItem)

    def test_init_none_storage_raises_error(self):
        """Test that None storage raises error."""
        with pytest.raises(Exception):
            _ItemNamespace("namespace", None, MockStoreItem)

    @pytest.mark.asyncio
    async def test_read_existing_key(self):
        """Test reading an existing key from namespaced storage."""
        storage = AsyncMock()
        base_key = "test_namespace"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        key = "test_key"
        mock_item = MockStoreItem({"data": "test_value"})
        
        # Mock the underlying storage to return the item
        storage.read.return_value = {f"{base_key}:{key}": mock_item}
        
        result = await item_namespace.read(key)
        
        assert result == mock_item
        storage.read.assert_called_once_with([f"{base_key}:{key}"], target_cls=MockStoreItem)

    @pytest.mark.asyncio
    async def test_read_missing_key(self):
        """Test reading a key that doesn't exist in namespaced storage."""
        storage = AsyncMock()
        base_key = "test_namespace"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        key = "missing_key"
        storage.read.return_value = {}  # Empty result for missing key
        
        result = await item_namespace.read(key)
        
        assert result is None
        storage.read.assert_called_once_with([f"{base_key}:{key}"], target_cls=MockStoreItem)

    @pytest.mark.asyncio
    async def test_write_item(self):
        """Test writing an item to namespaced storage."""
        storage = AsyncMock()
        base_key = "test_namespace"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        key = "test_key"
        item = MockStoreItem({"data": "test_value"})
        
        await item_namespace.write(key, item)
        
        storage.write.assert_called_once_with({f"{base_key}:{key}": item})

    @pytest.mark.asyncio
    async def test_delete_key(self):
        """Test deleting a key from namespaced storage."""
        storage = AsyncMock()
        base_key = "test_namespace"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        key = "test_key"
        
        await item_namespace.delete(key)
        
        storage.delete.assert_called_once_with([f"{base_key}:{key}"])

    @pytest.mark.asyncio
    async def test_integration_with_memory_storage(self):
        """Test integration with actual MemoryStorage."""
        memory_storage = MemoryStorage()
        base_key = "auth/channel123/user456"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        # Test data
        key = "oauth_state"
        item = MockStoreItem({"user": "alice", "state": "authorized"})
        
        # Initially, key should not exist
        result = await item_namespace.read(key)
        assert result is None
        
        # Write item
        await item_namespace.write(key, item)
        
        # Read item back
        result = await item_namespace.read(key)
        assert result == item
        assert result.data == {"user": "alice", "state": "authorized"}
        
        # Update item
        updated_item = MockStoreItem({"user": "alice", "state": "refreshed"})
        await item_namespace.write(key, updated_item)
        
        # Read updated item
        result = await item_namespace.read(key)
        assert result == updated_item
        assert result.data == {"user": "alice", "state": "refreshed"}
        
        # Delete item
        await item_namespace.delete(key)
        
        # Verify deletion
        result = await item_namespace.read(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_namespace_isolation(self):
        """Test that different namespaces are isolated from each other."""
        memory_storage = MemoryStorage()
        
        namespace1 = _ItemNamespace("auth/user1", memory_storage, MockStoreItem)
        namespace2 = _ItemNamespace("auth/user2", memory_storage, MockStoreItem)
        
        # Write same key to both namespaces
        key = "oauth_state"
        item1 = MockStoreItem({"user": "user1", "token": "token1"})
        item2 = MockStoreItem({"user": "user2", "token": "token2"})
        
        await namespace1.write(key, item1)
        await namespace2.write(key, item2)
        
        # Read from both namespaces
        result1 = await namespace1.read(key)
        result2 = await namespace2.read(key)
        
        # Verify isolation
        assert result1 == item1
        assert result2 == item2
        assert result1 != result2
        
        # Delete from one namespace shouldn't affect the other
        await namespace1.delete(key)
        
        result1_after = await namespace1.read(key)
        result2_after = await namespace2.read(key)
        
        assert result1_after is None
        assert result2_after == item2

    @pytest.mark.asyncio
    async def test_different_item_types_same_namespace(self):
        """Test different StoreItem types in the same namespace."""
        memory_storage = MemoryStorage()
        base_key = "shared_namespace"
        
        # Create namespaces with different item types
        namespace_a = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        namespace_b = _ItemNamespace(base_key, memory_storage, MockStoreItemB)
        
        # Write different item types to different keys
        item_a = MockStoreItem({"type": "A", "value": 123})
        item_b = MockStoreItemB({"type": "B", "value": 456}, other_field=False)
        
        await namespace_a.write("key_a", item_a)
        await namespace_b.write("key_b", item_b)
        
        # Read back items with their respective namespaces
        result_a = await namespace_a.read("key_a")
        result_b = await namespace_b.read("key_b")
        
        assert result_a == item_a
        assert result_b == item_b
        assert result_b.other_field is False
        
        # Verify that trying to read with wrong type fails gracefully
        # (This depends on the underlying storage implementation)
        result_cross = await namespace_a.read("key_b")
        # This might return None or raise an exception depending on implementation

    @pytest.mark.asyncio
    async def test_crud_operations_flow(self):
        """Test a complete CRUD flow with namespaced storage."""
        memory_storage = MemoryStorage()
        base_key = "flow_test"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        key = "session_data"
        
        # Create
        original_item = MockStoreItem({"status": "created", "version": 1})
        await item_namespace.write(key, original_item)
        
        # Read
        read_item = await item_namespace.read(key)
        assert read_item == original_item
        
        # Update
        updated_item = MockStoreItem({"status": "updated", "version": 2})
        await item_namespace.write(key, updated_item)
        
        # Read updated
        read_updated = await item_namespace.read(key)
        assert read_updated == updated_item
        assert read_updated != original_item
        
        # Delete
        await item_namespace.delete(key)
        
        # Read after delete
        read_after_delete = await item_namespace.read(key)
        assert read_after_delete is None

    @pytest.mark.asyncio
    async def test_multiple_keys_independence(self):
        """Test that different keys within the same namespace are independent."""
        memory_storage = MemoryStorage()
        base_key = "multi_key_test"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        # Write multiple items
        items = {
            "session1": MockStoreItem({"id": 1, "user": "alice"}),
            "session2": MockStoreItem({"id": 2, "user": "bob"}),
            "session3": MockStoreItem({"id": 3, "user": "charlie"})
        }
        
        for key, item in items.items():
            await item_namespace.write(key, item)
        
        # Verify all items exist
        for key, expected_item in items.items():
            result = await item_namespace.read(key)
            assert result == expected_item
        
        # Delete one item
        await item_namespace.delete("session2")
        
        # Verify only the deleted item is gone
        assert await item_namespace.read("session1") == items["session1"]
        assert await item_namespace.read("session2") is None
        assert await item_namespace.read("session3") == items["session3"]
        
        # Update one item
        updated_item = MockStoreItem({"id": 1, "user": "alice_updated"})
        await item_namespace.write("session1", updated_item)
        
        # Verify update doesn't affect other items
        assert await item_namespace.read("session1") == updated_item
        assert await item_namespace.read("session2") is None
        assert await item_namespace.read("session3") == items["session3"]

    @pytest.mark.asyncio
    async def test_complex_namespace_key_combinations(self):
        """Test various combinations of namespaces and keys."""
        memory_storage = MemoryStorage()
        
        test_cases = [
            ("auth/channel123/user456", "oauth_handler"),
            ("simple", "key_with_underscores"),
            ("namespace.with.dots", "key-with-dashes"),
            ("namespace:with:colons", "key:also:with:colons"),
            ("namespace with spaces", "key with spaces"),
            ("unicode_namespace_🔑", "unicode_key_🗝️")
        ]
        
        for base_key, key in test_cases:
            item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
            item = MockStoreItem({"namespace": base_key, "key": key})
            
            # Write item
            await item_namespace.write(key, item)
            
            # Read item back
            result = await item_namespace.read(key)
            assert result == item
            assert result.data["namespace"] == base_key
            assert result.data["key"] == key
            
            # Clean up for next iteration
            await item_namespace.delete(key)

    @pytest.mark.asyncio
    async def test_inheritance_from_item_storage(self):
        """Test that _ItemNamespace properly inherits from _ItemStorage."""
        memory_storage = MemoryStorage()
        base_key = "inheritance_test"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        # Verify that it has the expected methods from _ItemStorage
        assert hasattr(item_namespace, 'read')
        assert hasattr(item_namespace, 'write')
        assert hasattr(item_namespace, 'delete')
        assert hasattr(item_namespace, '_storage')
        assert hasattr(item_namespace, '_item_cls')
        
        # Test that the methods work as expected (basic functionality test)
        key = "test_key"
        item = MockStoreItem({"test": "data"})
        
        await item_namespace.write(key, item)
        result = await item_namespace.read(key)
        assert result == item
        
        await item_namespace.delete(key)
        result_after_delete = await item_namespace.read(key)
        assert result_after_delete is None

    @pytest.mark.asyncio
    async def test_storage_error_propagation(self):
        """Test that storage errors are properly propagated through the namespace wrapper."""
        storage = AsyncMock()
        base_key = "error_test"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        # Test read error propagation
        storage.read.side_effect = Exception("Storage read error")
        
        with pytest.raises(Exception, match="Storage read error"):
            await item_namespace.read("test_key")
        
        # Test write error propagation
        storage.read.side_effect = None  # Reset
        storage.write.side_effect = Exception("Storage write error")
        
        with pytest.raises(Exception, match="Storage write error"):
            await item_namespace.write("test_key", MockStoreItem({"data": "test"}))
        
        # Test delete error propagation
        storage.write.side_effect = None  # Reset
        storage.delete.side_effect = Exception("Storage delete error")
        
        with pytest.raises(Exception, match="Storage delete error"):
            await item_namespace.delete("test_key")

    def test_type_annotations(self):
        """Test that type annotations work correctly."""
        storage = MemoryStorage()
        base_key = "type_test"
        
        # Test generic type specification
        item_namespace_a: _ItemNamespace[MockStoreItem] = _ItemNamespace(base_key, storage, MockStoreItem)
        item_namespace_b: _ItemNamespace[MockStoreItemB] = _ItemNamespace(base_key, storage, MockStoreItemB)
        
        # Verify the generic types are properly set
        assert item_namespace_a._item_cls is MockStoreItem
        assert item_namespace_b._item_cls is MockStoreItemB

    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        memory_storage = MemoryStorage()
        base_key = "edge_test"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        # Test with very long key
        long_key = "x" * 1000
        long_item = MockStoreItem({"data": "long_key_data"})
        await item_namespace.write(long_key, long_item)
        result = await item_namespace.read(long_key)
        assert result == long_item
        
        # Test with empty data
        empty_data_item = MockStoreItem({})
        await item_namespace.write("empty_data", empty_data_item)
        result = await item_namespace.read("empty_data")
        assert result == empty_data_item
        assert result.data == {}
        
        # Test overwriting existing key multiple times
        key = "overwrite_test"
        for i in range(3):
            item = MockStoreItem({"version": i})
            await item_namespace.write(key, item)
            result = await item_namespace.read(key)
            assert result.data["version"] == i

    @pytest.mark.asyncio
    async def test_docstring_examples(self):
        """Test the examples that would be in docstrings."""
        memory_storage = MemoryStorage()
        base_key = "auth/channel123/user456"
        item_namespace = _ItemNamespace(base_key, memory_storage, MockStoreItem)
        
        # Example usage from docstrings
        key = "oauth_handler"
        
        # Reading non-existent key returns None
        result = await item_namespace.read(key)
        assert result is None
        
        # Write an item
        auth_data = MockStoreItem({
            "access_token": "abc123",
            "refresh_token": "def456",
            "expires_at": "2025-10-23T12:00:00Z",
            "scopes": ["read", "write"]
        })
        await item_namespace.write(key, auth_data)
        
        # Read the item back
        retrieved_data = await item_namespace.read(key)
        assert retrieved_data == auth_data
        assert retrieved_data.data["access_token"] == "abc123"
        
        # Delete the item
        await item_namespace.delete(key)
        
        # Verify deletion
        result_after_delete = await item_namespace.read(key)
        assert result_after_delete is None

    @pytest.mark.asyncio
    async def test_storage_namespace_key_prefixing(self):
        """Test that the underlying _StorageNamespace properly prefixes keys."""
        storage = AsyncMock()
        base_key = "test_namespace"
        item_namespace = _ItemNamespace(base_key, storage, MockStoreItem)
        
        key = "handler_id"
        item = MockStoreItem({"data": "test"})
        
        # Write operation should prefix the key
        await item_namespace.write(key, item)
        storage.write.assert_called_once_with({f"{base_key}:{key}": item})
        
        # Read operation should prefix the key
        storage.read.return_value = {f"{base_key}:{key}": item}
        result = await item_namespace.read(key)
        storage.read.assert_called_with([f"{base_key}:{key}"], target_cls=MockStoreItem)
        
        # Delete operation should prefix the key
        await item_namespace.delete(key)
        storage.delete.assert_called_with([f"{base_key}:{key}"])

    @pytest.mark.asyncio
    async def test_real_world_scenario(self):
        """Test a real-world scenario with user authentication state."""
        memory_storage = MemoryStorage()
        
        # Create namespaces for different users and channels
        user1_channel1 = _ItemNamespace("auth/channel1/user1", memory_storage, MockStoreItem)
        user2_channel1 = _ItemNamespace("auth/channel1/user2", memory_storage, MockStoreItem) 
        user1_channel2 = _ItemNamespace("auth/channel2/user1", memory_storage, MockStoreItem)
        
        # Store authentication state for different oauth handlers
        oauth_state_1 = MockStoreItem({
            "provider": "azure",
            "state": "authenticated",
            "access_token": "token1"
        })
        
        teams_state_1 = MockStoreItem({
            "provider": "teams", 
            "state": "authenticated",
            "access_token": "token2"
        })
        
        oauth_state_2 = MockStoreItem({
            "provider": "azure",
            "state": "pending",
            "access_token": None
        })
        
        # Write states for different users/channels
        await user1_channel1.write("oauth_handler", oauth_state_1)
        await user1_channel1.write("teams_handler", teams_state_1)
        await user2_channel1.write("oauth_handler", oauth_state_2)
        await user1_channel2.write("oauth_handler", oauth_state_1)
        
        # Verify isolation and correct retrieval
        assert await user1_channel1.read("oauth_handler") == oauth_state_1
        assert await user1_channel1.read("teams_handler") == teams_state_1
        assert await user2_channel1.read("oauth_handler") == oauth_state_2
        assert await user1_channel2.read("oauth_handler") == oauth_state_1
        
        # Verify that each user/channel has isolated state
        assert await user2_channel1.read("teams_handler") is None
        assert await user1_channel2.read("teams_handler") is None
        
        # Update one user's state and verify others are unaffected
        updated_oauth_state = MockStoreItem({
            "provider": "azure",
            "state": "refreshed", 
            "access_token": "new_token1"
        })
        await user1_channel1.write("oauth_handler", updated_oauth_state)
        
        assert await user1_channel1.read("oauth_handler") == updated_oauth_state
        assert await user2_channel1.read("oauth_handler") == oauth_state_2  # Unchanged
        assert await user1_channel2.read("oauth_handler") == oauth_state_1  # Unchanged
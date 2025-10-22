import pytest
import asyncio
from unittest.mock import AsyncMock

from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.storage._wrappers._item_storage import _ItemStorage
from tests._common.storage.utils import MockStoreItem, MockStoreItemB


class TestItemStorage:
    """Test cases for the _ItemStorage class."""

    def test_init_valid_params(self):
        """Test successful initialization with valid parameters."""
        storage = MemoryStorage()
        item_cls = MockStoreItem
        
        item_storage = _ItemStorage(storage, item_cls)
        
        assert item_storage._storage is storage
        assert item_storage._item_cls is item_cls

    def test_init_with_different_item_types(self):
        """Test initialization with different StoreItem types."""
        storage = MemoryStorage()
        
        # Test with MockStoreItem
        item_storage_a = _ItemStorage(storage, MockStoreItem)
        assert item_storage_a._item_cls is MockStoreItem
        
        # Test with MockStoreItemB
        item_storage_b = _ItemStorage(storage, MockStoreItemB)
        assert item_storage_b._item_cls is MockStoreItemB

    @pytest.mark.asyncio
    async def test_read_existing_key(self):
        """Test reading an existing key from storage."""
        storage = AsyncMock()
        item_cls = MockStoreItem
        item_storage = _ItemStorage(storage, item_cls)
        
        key = "test_key"
        mock_item = MockStoreItem({"data": "test_value"})
        storage.read.return_value = {key: mock_item}
        
        result = await item_storage.read(key)
        
        assert result == mock_item
        storage.read.assert_called_once_with([key], target_cls=item_cls)

    @pytest.mark.asyncio
    async def test_read_missing_key(self):
        """Test reading a key that doesn't exist in storage."""
        storage = AsyncMock()
        item_cls = MockStoreItem
        item_storage = _ItemStorage(storage, item_cls)
        
        key = "missing_key"
        storage.read.return_value = {}  # Empty result for missing key
        
        result = await item_storage.read(key)
        
        assert result is None
        storage.read.assert_called_once_with([key], target_cls=item_cls)

    @pytest.mark.asyncio
    async def test_read_with_different_item_types(self):
        """Test reading with different StoreItem types."""
        storage = AsyncMock()
        
        # Test with MockStoreItem
        item_storage_a = _ItemStorage(storage, MockStoreItem)
        mock_item_a = MockStoreItem({"type": "A"})
        storage.read.return_value = {"key": mock_item_a}
        
        result_a = await item_storage_a.read("key")
        assert result_a == mock_item_a
        storage.read.assert_called_with(["key"], target_cls=MockStoreItem)
        
        # Reset mock and test with MockStoreItemB
        storage.reset_mock()
        item_storage_b = _ItemStorage(storage, MockStoreItemB)
        mock_item_b = MockStoreItemB({"type": "B"}, other_field=False)
        storage.read.return_value = {"key": mock_item_b}
        
        result_b = await item_storage_b.read("key")
        assert result_b == mock_item_b
        storage.read.assert_called_with(["key"], target_cls=MockStoreItemB)

    @pytest.mark.asyncio
    async def test_write_item(self):
        """Test writing an item to storage."""
        storage = AsyncMock()
        item_cls = MockStoreItem
        item_storage = _ItemStorage(storage, item_cls)
        
        key = "test_key"
        item = MockStoreItem({"data": "test_value"})
        
        await item_storage.write(key, item)
        
        storage.write.assert_called_once_with({key: item})

    @pytest.mark.asyncio
    async def test_write_different_item_types(self):
        """Test writing different StoreItem types."""
        storage = AsyncMock()
        
        # Test with MockStoreItem
        item_storage_a = _ItemStorage(storage, MockStoreItem)
        item_a = MockStoreItem({"type": "A"})
        
        await item_storage_a.write("key_a", item_a)
        storage.write.assert_called_with({"key_a": item_a})
        
        # Reset mock and test with MockStoreItemB
        storage.reset_mock()
        item_storage_b = _ItemStorage(storage, MockStoreItemB)
        item_b = MockStoreItemB({"type": "B"}, other_field=True)
        
        await item_storage_b.write("key_b", item_b)
        storage.write.assert_called_with({"key_b": item_b})

    @pytest.mark.asyncio
    async def test_delete_key(self):
        """Test deleting a key from storage."""
        storage = AsyncMock()
        item_cls = MockStoreItem
        item_storage = _ItemStorage(storage, item_cls)
        
        key = "test_key"
        
        await item_storage.delete(key)
        
        storage.delete.assert_called_once_with([key])

    @pytest.mark.asyncio
    async def test_delete_multiple_calls(self):
        """Test deleting multiple keys with separate calls."""
        storage = AsyncMock()
        item_cls = MockStoreItem
        item_storage = _ItemStorage(storage, item_cls)
        
        keys = ["key1", "key2", "key3"]
        
        for key in keys:
            await item_storage.delete(key)
        
        # Each delete call should be made separately
        expected_calls = [([key],) for key in keys]
        actual_calls = [call.args for call in storage.delete.call_args_list]
        assert actual_calls == expected_calls
        assert storage.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_integration_with_memory_storage(self):
        """Test integration with actual MemoryStorage."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        # Test data
        key = "test_key"
        item = MockStoreItem({"user": "alice", "data": "test_data"})
        
        # Initially, key should not exist
        result = await item_storage.read(key)
        assert result is None
        
        # Write item
        await item_storage.write(key, item)
        
        # Read item back
        result = await item_storage.read(key)
        assert result == item
        assert result.data == {"user": "alice", "data": "test_data"}
        
        # Update item
        updated_item = MockStoreItem({"user": "alice", "data": "updated_data"})
        await item_storage.write(key, updated_item)
        
        # Read updated item
        result = await item_storage.read(key)
        assert result == updated_item
        assert result.data == {"user": "alice", "data": "updated_data"}
        
        # Delete item
        await item_storage.delete(key)
        
        # Verify deletion
        result = await item_storage.read(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_integration_with_different_item_types(self):
        """Test integration with different StoreItem types."""
        memory_storage = MemoryStorage()
        
        # Test with MockStoreItem
        item_storage_a = _ItemStorage(memory_storage, MockStoreItem)
        item_a = MockStoreItem({"type": "A", "value": 123})
        
        await item_storage_a.write("key_a", item_a)
        result_a = await item_storage_a.read("key_a")
        assert result_a == item_a
        
        # Test with MockStoreItemB - same underlying storage
        item_storage_b = _ItemStorage(memory_storage, MockStoreItemB)
        item_b = MockStoreItemB({"type": "B", "value": 456}, other_field=False)
        
        await item_storage_b.write("key_b", item_b)
        result_b = await item_storage_b.read("key_b")
        assert result_b == item_b
        assert result_b.other_field is False
        
        # Verify both items exist in the same storage
        # Note: We can't cross-read different types due to target_cls mismatch
        # but we can verify they don't interfere with each other
        result_a_after = await item_storage_a.read("key_a")
        assert result_a_after == item_a

    @pytest.mark.asyncio
    async def test_crud_operations_flow(self):
        """Test a complete CRUD flow."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        key = "flow_test_key"
        
        # Create
        original_item = MockStoreItem({"status": "created", "version": 1})
        await item_storage.write(key, original_item)
        
        # Read
        read_item = await item_storage.read(key)
        assert read_item == original_item
        
        # Update
        updated_item = MockStoreItem({"status": "updated", "version": 2})
        await item_storage.write(key, updated_item)
        
        # Read updated
        read_updated = await item_storage.read(key)
        assert read_updated == updated_item
        assert read_updated != original_item
        
        # Delete
        await item_storage.delete(key)
        
        # Read after delete
        read_after_delete = await item_storage.read(key)
        assert read_after_delete is None

    @pytest.mark.asyncio
    async def test_multiple_keys_independence(self):
        """Test that different keys are independent."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        # Write multiple items
        items = {
            "key1": MockStoreItem({"id": 1, "name": "first"}),
            "key2": MockStoreItem({"id": 2, "name": "second"}),
            "key3": MockStoreItem({"id": 3, "name": "third"})
        }
        
        for key, item in items.items():
            await item_storage.write(key, item)
        
        # Verify all items exist
        for key, expected_item in items.items():
            result = await item_storage.read(key)
            assert result == expected_item
        
        # Delete one item
        await item_storage.delete("key2")
        
        # Verify only the deleted item is gone
        assert await item_storage.read("key1") == items["key1"]
        assert await item_storage.read("key2") is None
        assert await item_storage.read("key3") == items["key3"]
        
        # Update one item
        updated_item = MockStoreItem({"id": 1, "name": "updated_first"})
        await item_storage.write("key1", updated_item)
        
        # Verify update doesn't affect other items
        assert await item_storage.read("key1") == updated_item
        assert await item_storage.read("key2") is None
        assert await item_storage.read("key3") == items["key3"]

    @pytest.mark.asyncio
    async def test_key_variations(self):
        """Test various key formats and special characters."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        test_keys = [
            "simple",
            "key_with_underscores",
            "key-with-dashes",
            "key.with.dots",
            "key/with/slashes",
            "key:with:colons",
            "key with spaces",
            "KEY_UPPERCASE",
            "key123numbers",
            "special!@#$%chars",
            "unicode_key_🔑",
            "empty_value_key"
        ]
        
        # Write items with various keys
        for i, key in enumerate(test_keys):
            item = MockStoreItem({"key_id": i, "key_name": key})
            await item_storage.write(key, item)
        
        # Read back and verify
        for i, key in enumerate(test_keys):
            result = await item_storage.read(key)
            assert result is not None
            assert result.data["key_id"] == i
            assert result.data["key_name"] == key

    @pytest.mark.asyncio
    async def test_storage_error_propagation(self):
        """Test that storage errors are properly propagated."""
        storage = AsyncMock()
        item_storage = _ItemStorage(storage, MockStoreItem)
        
        # Test read error propagation
        storage.read.side_effect = Exception("Storage read error")
        
        with pytest.raises(Exception, match="Storage read error"):
            await item_storage.read("test_key")
        
        # Test write error propagation
        storage.read.side_effect = None  # Reset
        storage.write.side_effect = Exception("Storage write error")
        
        with pytest.raises(Exception, match="Storage write error"):
            await item_storage.write("test_key", MockStoreItem({"data": "test"}))
        
        # Test delete error propagation
        storage.write.side_effect = None  # Reset
        storage.delete.side_effect = Exception("Storage delete error")
        
        with pytest.raises(Exception, match="Storage delete error"):
            await item_storage.delete("test_key")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations on the same storage."""
        
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        # Define concurrent operations
        async def write_operation(key_suffix: int):
            item = MockStoreItem({"id": key_suffix, "data": f"data_{key_suffix}"})
            await item_storage.write(f"concurrent_key_{key_suffix}", item)
        
        async def read_operation(key_suffix: int):
            return await item_storage.read(f"concurrent_key_{key_suffix}")
        
        # Execute concurrent writes
        write_tasks = [write_operation(i) for i in range(5)]
        await asyncio.gather(*write_tasks)
        
        # Execute concurrent reads
        read_tasks = [read_operation(i) for i in range(5)]
        results = await asyncio.gather(*read_tasks)
        
        # Verify all operations completed successfully
        for i, result in enumerate(results):
            assert result is not None
            assert result.data["id"] == i
            assert result.data["data"] == f"data_{i}"

    def test_type_annotations(self):
        """Test that type annotations work correctly."""
        storage = MemoryStorage()
        
        # Test generic type specification
        item_storage_a: _ItemStorage[MockStoreItem] = _ItemStorage(storage, MockStoreItem)
        item_storage_b: _ItemStorage[MockStoreItemB] = _ItemStorage(storage, MockStoreItemB)
        
        # Verify the generic types are properly set
        assert item_storage_a._item_cls is MockStoreItem
        assert item_storage_b._item_cls is MockStoreItemB
        
        # This test mainly verifies that the type annotations don't cause runtime errors
        # The actual type checking would be done by a static type checker like mypy

    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        # Test with very long key
        long_key = "x" * 1000
        long_item = MockStoreItem({"data": "long_key_data"})
        await item_storage.write(long_key, long_item)
        result = await item_storage.read(long_key)
        assert result == long_item
        
        # Test with empty data
        empty_data_item = MockStoreItem({})
        await item_storage.write("empty_data", empty_data_item)
        result = await item_storage.read("empty_data")
        assert result == empty_data_item
        assert result
        assert result.data == {}
        
        # Test overwriting existing key multiple times
        key = "overwrite_test"
        for i in range(3):
            item = MockStoreItem({"version": i})
            await item_storage.write(key, item)
            result = await item_storage.read(key)
            assert result.data["version"] == i

    @pytest.mark.asyncio
    async def test_docstring_examples(self):
        """Test the examples that would be in docstrings."""
        memory_storage = MemoryStorage()
        item_storage = _ItemStorage(memory_storage, MockStoreItem)
        
        # Example usage from docstrings
        key = "user_session_123"
        
        # Reading non-existent key returns None
        result = await item_storage.read(key)
        assert result is None
        
        # Write an item
        session_data = MockStoreItem({
            "user_id": "123",
            "login_time": "2025-10-22T10:00:00Z",
            "permissions": ["read", "write"]
        })
        await item_storage.write(key, session_data)
        
        # Read the item back
        retrieved_data = await item_storage.read(key)
        assert retrieved_data == session_data
        assert retrieved_data
        assert retrieved_data.data["user_id"] == "123"
        
        # Delete the item
        await item_storage.delete(key)
        
        # Verify deletion
        result_after_delete = await item_storage.read(key)
        assert result_after_delete is None
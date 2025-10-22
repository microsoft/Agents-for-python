import pytest
from unittest.mock import Mock, AsyncMock

from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.storage._wrappers._storage_namespace import _StorageNamespace
from tests._common.storage.utils import MockStoreItem


class TestStorageNamespace:
    """Test cases for the _StorageNamespace class."""

    def test_init_valid_params(self):
        """Test successful initialization with valid parameters."""
        storage = MemoryStorage()
        namespace = "test_namespace"
        
        storage_namespace = _StorageNamespace(namespace, storage)
        
        assert storage_namespace.base_key == namespace

    def test_init_empty_namespace_raises_error(self):
        """Test that empty namespace raises ValueError."""
        storage = MemoryStorage()
        
        with pytest.raises(ValueError):
            _StorageNamespace("", storage)

    def test_init_none_namespace_raises_error(self):
        """Test that None namespace raises ValueError."""
        storage = MemoryStorage()
        
        with pytest.raises(ValueError):
            _StorageNamespace(None, storage)

    def test_init_none_storage_raises_error(self):
        """Test that None storage raises error from _raise_if_falsey."""
        # This would raise an error from _raise_if_falsey function
        with pytest.raises(Exception):  # Could be ValueError or another exception type
            _StorageNamespace("namespace", None)

    def test_base_key_property(self):
        """Test the base_key property returns the correct value."""
        namespace = "auth/channel123/user456"
        storage = MemoryStorage()
        
        storage_namespace = _StorageNamespace(namespace, storage)
        
        assert storage_namespace.base_key == namespace

    def test_key_method(self):
        """Test the key method creates proper storage keys."""
        namespace = "test_namespace"
        storage = MemoryStorage()
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "handler_id"
        expected_key = "test_namespace:handler_id"
        
        assert storage_namespace.key(vkey) == expected_key

    def test_key_method_with_complex_namespace(self):
        """Test the key method with complex namespace."""
        namespace = "auth/channel123/user456"
        storage = MemoryStorage()
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "oauth_handler"
        expected_key = "auth/channel123/user456:oauth_handler"
        
        assert storage_namespace.key(vkey) == expected_key

    @pytest.mark.asyncio
    async def test_read_single_key(self):
        """Test reading a single key."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "handler1"
        expected_storage_key = "test_namespace:handler1"
        mock_item = MockStoreItem({"data": "test"})
        
        storage.read.return_value = {expected_storage_key: mock_item}
        
        result = await storage_namespace.read([vkey], target_cls=MockStoreItem)
        
        assert result == {vkey: mock_item}
        storage.read.assert_called_once_with([expected_storage_key], target_cls=MockStoreItem)

    @pytest.mark.asyncio
    async def test_read_multiple_keys(self):
        """Test reading multiple keys."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkeys = ["handler1", "handler2", "handler3"]
        expected_storage_keys = [
            "test_namespace:handler1",
            "test_namespace:handler2", 
            "test_namespace:handler3"
        ]
        mock_items = {
            expected_storage_keys[0]: MockStoreItem({"data": "test1"}),
            expected_storage_keys[1]: MockStoreItem({"data": "test2"}),
            expected_storage_keys[2]: MockStoreItem({"data": "test3"})
        }
        
        storage.read.return_value = mock_items
        
        result = await storage_namespace.read(vkeys, target_cls=MockStoreItem)
        
        expected_result = {
            "handler1": mock_items[expected_storage_keys[0]],
            "handler2": mock_items[expected_storage_keys[1]],
            "handler3": mock_items[expected_storage_keys[2]]
        }
        assert result == expected_result
        storage.read.assert_called_once_with(expected_storage_keys, target_cls=MockStoreItem)

    @pytest.mark.asyncio
    async def test_read_missing_keys(self):
        """Test reading keys that don't exist in storage."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkeys = ["missing1", "missing2"]
        storage.read.return_value = {}  # No items found
        
        result = await storage_namespace.read(vkeys, target_cls=MockStoreItem)
        
        assert result == {}
        storage.read.assert_called_once_with(
            ["test_namespace:missing1", "test_namespace:missing2"], 
            target_cls=MockStoreItem
        )

    @pytest.mark.asyncio
    async def test_read_partial_results(self):
        """Test reading where only some keys exist."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkeys = ["exists", "missing"]
        mock_item = MockStoreItem({"data": "found"})
        storage.read.return_value = {"test_namespace:exists": mock_item}
        
        result = await storage_namespace.read(vkeys, target_cls=MockStoreItem)
        
        assert result == {"exists": mock_item}
        storage.read.assert_called_once_with(
            ["test_namespace:exists", "test_namespace:missing"], 
            target_cls=MockStoreItem
        )

    @pytest.mark.asyncio
    async def test_read_with_kwargs(self):
        """Test reading with additional keyword arguments."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "handler1"
        mock_item = MockStoreItem({"data": "test"})
        storage.read.return_value = {"test_namespace:handler1": mock_item}
        
        await storage_namespace.read([vkey], target_cls=MockStoreItem, extra_param="value")
        
        storage.read.assert_called_once_with(
            ["test_namespace:handler1"], 
            target_cls=MockStoreItem, 
            extra_param="value"
        )

    @pytest.mark.asyncio
    async def test_write_single_item(self):
        """Test writing a single item."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "handler1"
        item = MockStoreItem({"data": "test"})
        changes = {vkey: item}
        
        await storage_namespace.write(changes)
        
        expected_storage_changes = {"test_namespace:handler1": item}
        storage.write.assert_called_once_with(expected_storage_changes)

    @pytest.mark.asyncio
    async def test_write_multiple_items(self):
        """Test writing multiple items."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        changes = {
            "handler1": MockStoreItem({"data": "test1"}),
            "handler2": MockStoreItem({"data": "test2"}),
            "handler3": MockStoreItem({"data": "test3"})
        }
        
        await storage_namespace.write(changes)
        
        expected_storage_changes = {
            "test_namespace:handler1": changes["handler1"],
            "test_namespace:handler2": changes["handler2"],
            "test_namespace:handler3": changes["handler3"]
        }
        storage.write.assert_called_once_with(expected_storage_changes)

    @pytest.mark.asyncio
    async def test_write_empty_changes(self):
        """Test writing with empty changes dictionary."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        await storage_namespace.write({})
        
        storage.write.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_delete_single_key(self):
        """Test deleting a single key."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkey = "handler1"
        
        await storage_namespace.delete([vkey])
        
        storage.delete.assert_called_once_with(["test_namespace:handler1"])

    @pytest.mark.asyncio
    async def test_delete_multiple_keys(self):
        """Test deleting multiple keys."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        vkeys = ["handler1", "handler2", "handler3"]
        
        await storage_namespace.delete(vkeys)
        
        expected_storage_keys = [
            "test_namespace:handler1",
            "test_namespace:handler2",
            "test_namespace:handler3"
        ]
        storage.delete.assert_called_once_with(expected_storage_keys)

    @pytest.mark.asyncio
    async def test_delete_empty_keys(self):
        """Test deleting with empty keys list."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        await storage_namespace.delete([])
        
        storage.delete.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_integration_with_memory_storage(self):
        """Test integration with actual MemoryStorage."""
        memory_storage = MemoryStorage()
        namespace = "auth/channel123/user456"
        storage_namespace = _StorageNamespace(namespace, memory_storage)
        
        # Test data
        item1 = MockStoreItem({"user": "alice", "state": "active"})
        item2 = MockStoreItem({"user": "bob", "state": "inactive"})
        
        # Write items
        await storage_namespace.write({
            "oauth_handler": item1,
            "teams_handler": item2
        })
        
        # Read items back
        result = await storage_namespace.read(
            ["oauth_handler", "teams_handler"], 
            target_cls=MockStoreItem
        )
        
        assert len(result) == 2
        assert result["oauth_handler"] == item1
        assert result["teams_handler"] == item2
        
        # Read non-existent item
        missing_result = await storage_namespace.read(["missing"], target_cls=MockStoreItem)
        assert missing_result == {}
        
        # Delete one item
        await storage_namespace.delete(["oauth_handler"])
        
        # Verify deletion
        after_delete = await storage_namespace.read(
            ["oauth_handler", "teams_handler"], 
            target_cls=MockStoreItem
        )
        assert len(after_delete) == 1
        assert "oauth_handler" not in after_delete
        assert after_delete["teams_handler"] == item2

    @pytest.mark.asyncio
    async def test_namespace_isolation(self):
        """Test that different namespaces are isolated from each other."""
        memory_storage = MemoryStorage()
        
        namespace1 = _StorageNamespace("namespace1", memory_storage)
        namespace2 = _StorageNamespace("namespace2", memory_storage)
        
        # Write same key to both namespaces
        item1 = MockStoreItem({"source": "namespace1"})
        item2 = MockStoreItem({"source": "namespace2"})
        
        await namespace1.write({"shared_key": item1})
        await namespace2.write({"shared_key": item2})
        
        # Read from both namespaces
        result1 = await namespace1.read(["shared_key"], target_cls=MockStoreItem)
        result2 = await namespace2.read(["shared_key"], target_cls=MockStoreItem)
        
        # Verify isolation
        assert result1["shared_key"] == item1
        assert result2["shared_key"] == item2
        assert result1["shared_key"] != result2["shared_key"]
        
        # Delete from one namespace shouldn't affect the other
        await namespace1.delete(["shared_key"])
        
        result1_after = await namespace1.read(["shared_key"], target_cls=MockStoreItem)
        result2_after = await namespace2.read(["shared_key"], target_cls=MockStoreItem)
        
        assert result1_after == {}
        assert result2_after["shared_key"] == item2

    @pytest.mark.asyncio
    async def test_key_with_colon_in_vkey(self):
        """Test behavior when virtual key contains colon."""
        storage = AsyncMock()
        namespace = "test_namespace"
        storage_namespace = _StorageNamespace(namespace, storage)
        
        # Virtual key with colon
        vkey = "oauth:handler:v2"
        mock_item = MockStoreItem({"data": "test"})
        
        # The storage key will be "test_namespace:oauth:handler:v2"
        storage_key = "test_namespace:oauth:handler:v2"
        storage.read.return_value = {storage_key: mock_item}
        
        result = await storage_namespace.read([vkey], target_cls=MockStoreItem)
        
        # Should correctly extract the virtual key from storage key
        assert result == {vkey: mock_item}
        storage.read.assert_called_once_with([storage_key], target_cls=MockStoreItem)

    def test_different_namespace_formats(self):
        """Test different namespace format patterns."""
        storage = MemoryStorage()
        
        test_cases = [
            "simple",
            "auth/channel123/user456",
            "oauth.handler.state",
            "nested:namespace:with:colons",
            "namespace_with_underscores",
            "namespace-with-dashes"
        ]
        
        for namespace in test_cases:
            storage_namespace = _StorageNamespace(namespace, storage)
            assert storage_namespace.base_key == namespace
            
            vkey = "test_key"
            expected_key = f"{namespace}:{vkey}"
            assert storage_namespace.key(vkey) == expected_key
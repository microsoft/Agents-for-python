# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import unittest
from unittest.mock import Mock, AsyncMock, patch, mock_open
import json
from typing import Dict, Any

from azure.cosmos import documents, http_constants
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
import azure.cosmos.exceptions as cosmos_exceptions

from microsoft.agents.storage import StoreItem
from cosmos import CosmosDBConfig, CosmosDBStorage, sanitize_key, truncate_key


class MockStoreItem(StoreItem):
    """Mock StoreItem for testing"""
    
    def __init__(self, data: Dict[str, Any] = None):
        self.data = data or {}
        self.e_tag = "*"
    
    @classmethod
    def from_json_to_store_item(cls, json_data: Dict[str, Any]) -> 'MockStoreItem':
        item = cls()
        item.data = json_data
        return item
    
    def store_item_to_json(self) -> Dict[str, Any]:
        return self.data


class TestCosmosDBConfig(unittest.TestCase):
    """Test cases for CosmosDBConfig class"""
    
    def test_config_initialization_with_parameters(self):
        """Test basic configuration initialization"""
        config = CosmosDBConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
            container_throughput=800,
            key_suffix="_test",
            compatibility_mode=True
        )
        
        self.assertEqual(config.cosmos_db_endpoint, "https://test.documents.azure.com:443/")
        self.assertEqual(config.auth_key, "test_key")
        self.assertEqual(config.database_id, "test_db")
        self.assertEqual(config.container_id, "test_container")
        self.assertEqual(config.container_throughput, 800)
        self.assertEqual(config.key_suffix, "_test")
        self.assertTrue(config.compatibility_mode)
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"cosmos_db_endpoint": "https://file.test.com", "auth_key": "file_key"}')
    def test_config_initialization_from_file(self, mock_file):
        """Test configuration initialization from JSON file"""
        config = CosmosDBConfig(filename="test_config.json")
        
        self.assertEqual(config.cosmos_db_endpoint, "https://file.test.com")
        self.assertEqual(config.auth_key, "file_key")
        mock_file.assert_called_once_with("test_config.json")
    
    def test_config_parameter_override_file(self):
        """Test that direct parameters override file parameters"""
        with patch("builtins.open", new_callable=mock_open, read_data='{"cosmos_db_endpoint": "https://file.test.com"}'):
            config = CosmosDBConfig(
                cosmos_db_endpoint="https://override.test.com",
                filename="test_config.json"
            )
            
            self.assertEqual(config.cosmos_db_endpoint, "https://override.test.com")


class TestKeySanitization(unittest.TestCase):
    """Test cases for key sanitization functions"""
    
    def test_sanitize_key_normal_string(self):
        """Test sanitization of normal string"""
        result = sanitize_key("normal_key", compatibility_mode=False)
        self.assertEqual(result, "normal_key")
    
    def test_sanitize_key_with_forbidden_chars(self):
        """Test sanitization of string with forbidden characters"""
        result = sanitize_key("key\\with?bad/chars#", compatibility_mode=False)
        expected = "key*92with*63bad*47chars*35"
        self.assertEqual(result, expected)
    
    def test_sanitize_key_with_suffix(self):
        """Test sanitization with key suffix"""
        result = sanitize_key("test_key", key_suffix="_suffix", compatibility_mode=False)
        self.assertEqual(result, "test_key_suffix")
    
    def test_sanitize_key_with_tabs_and_newlines(self):
        """Test sanitization of tabs and newlines"""
        result = sanitize_key("key\twith\nnewlines\rand\ttabs", compatibility_mode=False)
        expected = "key*9with*10newlines*13and*9tabs"
        self.assertEqual(result, expected)
    
    def test_truncate_key_short_string(self):
        """Test truncation of short string"""
        result = truncate_key("short_key", compatibility_mode=True)
        self.assertEqual(result, "short_key")
    
    def test_truncate_key_long_string(self):
        """Test truncation of long string"""
        long_key = "a" * 300
        result = truncate_key(long_key, compatibility_mode=True)
        
        # Should be exactly 255 characters
        self.assertEqual(len(result), 255)
        # Should end with a hash
        self.assertTrue(result.endswith("aa" * 16))  # SHA256 hex is 64 chars, but truncated
    
    def test_truncate_key_disabled(self):
        """Test truncation when compatibility mode is disabled"""
        long_key = "a" * 300
        result = truncate_key(long_key, compatibility_mode=False)
        self.assertEqual(result, long_key)
        self.assertEqual(len(result), 300)


class TestCosmosDBStorage(unittest.TestCase):
    """Test cases for CosmosDBStorage class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CosmosDBConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container"
        )
        
        self.mock_client = Mock(spec=CosmosClient)
        self.mock_database = Mock(spec=DatabaseProxy)
        self.mock_container = Mock(spec=ContainerProxy)
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        # Should not raise any exception
        CosmosDBStorage._validate_config(self.config)
    
    def test_config_validation_missing_config(self):
        """Test validation with missing config"""
        with self.assertRaises(ValueError) as cm:
            CosmosDBStorage._validate_config(None)
        self.assertIn("CosmosDBConfig is required", str(cm.exception))
    
    def test_config_validation_missing_endpoint(self):
        """Test validation with missing endpoint"""
        config = CosmosDBConfig(auth_key="key", database_id="db", container_id="container")
        with self.assertRaises(ValueError) as cm:
            CosmosDBStorage._validate_config(config)
        self.assertIn("cosmos_db_endpoint is required", str(cm.exception))
    
    def test_config_validation_missing_auth_key(self):
        """Test validation with missing auth key"""
        config = CosmosDBConfig(cosmos_db_endpoint="endpoint", database_id="db", container_id="container")
        with self.assertRaises(ValueError) as cm:
            CosmosDBStorage._validate_config(config)
        self.assertIn("auth_key is required", str(cm.exception))
    
    def test_suffix_validation_success(self):
        """Test successful suffix validation"""
        config = CosmosDBConfig(key_suffix="valid_suffix", compatibility_mode=False)
        # Should not raise any exception
        CosmosDBStorage._validate_suffix(config)
    
    def test_suffix_validation_with_compatibility_mode(self):
        """Test suffix validation fails with compatibility mode"""
        config = CosmosDBConfig(key_suffix="suffix", compatibility_mode=True)
        with self.assertRaises(ValueError) as cm:
            CosmosDBStorage._validate_suffix(config)
        self.assertIn("compatibilityMode cannot be true while using a keySuffix", str(cm.exception))
    
    def test_suffix_validation_invalid_characters(self):
        """Test suffix validation with invalid characters"""
        config = CosmosDBConfig(key_suffix="bad\\suffix", compatibility_mode=False)
        with self.assertRaises(ValueError) as cm:
            CosmosDBStorage._validate_suffix(config)
        self.assertIn("Cannot use invalid Row Key characters", str(cm.exception))
    
    @patch('cosmos.CosmosClient')
    def test_create_client_success(self, mock_cosmos_client):
        """Test successful client creation"""
        storage = CosmosDBStorage(self.config)
        client = storage._create_client()
        
        mock_cosmos_client.assert_called_once()
        args, kwargs = mock_cosmos_client.call_args
        self.assertEqual(args[0], self.config.cosmos_db_endpoint)
        self.assertEqual(args[1], self.config.auth_key)
    
    @patch('cosmos.CosmosClient')
    def test_storage_initialization(self, mock_cosmos_client):
        """Test storage initialization"""
        mock_cosmos_client.return_value = self.mock_client
        
        storage = CosmosDBStorage(self.config)
        
        self.assertEqual(storage._config, self.config)
        self.assertIsNotNone(storage._client)
        self.assertIsNone(storage._database)
        self.assertIsNone(storage._container)
        self.assertFalse(storage._compatability_mode_partition_key)


class TestCosmosDBStorageAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for CosmosDBStorage class"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.config = CosmosDBConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container"
        )
        
        self.mock_client = Mock(spec=CosmosClient)
        self.mock_database = Mock(spec=DatabaseProxy)
        self.mock_container = Mock(spec=ContainerProxy)
        
        # Configure async mocks
        self.mock_container.read_item = AsyncMock()
        self.mock_container.upsert_item = AsyncMock()
        self.mock_container.delete_item = AsyncMock()
        self.mock_container.read = Mock()
        
        self.mock_database.create_container = Mock()
        self.mock_database.get_container_client = Mock()
        
        self.mock_client.create_database_if_not_exists = Mock()
    
    @patch('cosmos.CosmosClient')
    async def test_read_success(self, mock_cosmos_client):
        """Test successful read operation"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        self.mock_database.create_container.return_value = self.mock_container
        
        # Mock the read response
        mock_response = {
            "realId": "test_key",
            "document": {"data": "test_data"}
        }
        self.mock_container.read_item.return_value = mock_response
        
        storage = CosmosDBStorage(self.config)
        result = await storage.read(["test_key"], target_cls=MockStoreItem)
        
        self.assertIn("test_key", result)
        self.assertEqual(result["test_key"].data, {"data": "test_data"})
    
    @patch('cosmos.CosmosClient')
    async def test_read_empty_keys(self, mock_cosmos_client):
        """Test read with empty keys list"""
        mock_cosmos_client.return_value = self.mock_client
        
        storage = CosmosDBStorage(self.config)
        
        with self.assertRaises(ValueError) as cm:
            await storage.read([])
        self.assertIn("keys cannot be None or empty", str(cm.exception))
    
    @patch('cosmos.CosmosClient')
    async def test_write_success(self, mock_cosmos_client):
        """Test successful write operation"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        self.mock_database.create_container.return_value = self.mock_container
        
        storage = CosmosDBStorage(self.config)
        
        test_item = MockStoreItem({"test": "data"})
        changes = {"test_key": test_item}
        
        await storage.write(changes)
        
        # Verify upsert_item was called
        self.mock_container.upsert_item.assert_called_once()
        args, kwargs = self.mock_container.upsert_item.call_args
        
        # Check the document structure
        doc = kwargs.get('body') or args[0] if args else None
        self.assertIsNotNone(doc)
        self.assertEqual(doc["realId"], "test_key")
        self.assertEqual(doc["document"], {"test": "data"})
    
    @patch('cosmos.CosmosClient')
    async def test_write_empty_changes(self, mock_cosmos_client):
        """Test write with empty changes"""
        mock_cosmos_client.return_value = self.mock_client
        
        storage = CosmosDBStorage(self.config)
        
        with self.assertRaises(Exception) as cm:
            await storage.write({})
        self.assertIn("Changes are required when writing", str(cm.exception))
    
    @patch('cosmos.CosmosClient')
    async def test_delete_success(self, mock_cosmos_client):
        """Test successful delete operation"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        self.mock_database.create_container.return_value = self.mock_container
        
        storage = CosmosDBStorage(self.config)
        
        await storage.delete(["test_key1", "test_key2"])
        
        # Verify delete_item was called for each key
        self.assertEqual(self.mock_container.delete_item.call_count, 2)
    
    @patch('cosmos.CosmosClient')
    async def test_delete_none_keys(self, mock_cosmos_client):
        """Test delete with None keys"""
        mock_cosmos_client.return_value = self.mock_client
        
        storage = CosmosDBStorage(self.config)
        
        with self.assertRaises(ValueError) as cm:
            await storage.delete(None)
        self.assertIn("keys parameter can't be null", str(cm.exception))
    
    @patch('cosmos.CosmosClient')
    async def test_initialize_new_container(self, mock_cosmos_client):
        """Test initialization with new container creation"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        self.mock_database.create_container.return_value = self.mock_container
        
        storage = CosmosDBStorage(self.config)
        await storage.initialize()
        
        # Verify database and container creation
        self.mock_client.create_database_if_not_exists.assert_called_once_with("test_db")
        self.mock_database.create_container.assert_called_once()
        
        # Check partition key configuration
        args, kwargs = self.mock_database.create_container.call_args
        partition_key = args[1]
        self.assertEqual(partition_key["paths"], ["/id"])
        self.assertEqual(partition_key["kind"], documents.PartitionKind.Hash)
    
    @patch('cosmos.CosmosClient')
    async def test_initialize_existing_container_conflict(self, mock_cosmos_client):
        """Test initialization with existing container (conflict scenario)"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        
        # Mock conflict exception
        conflict_error = cosmos_exceptions.CosmosHttpResponseError(
            status_code=http_constants.StatusCodes.CONFLICT
        )
        self.mock_database.create_container.side_effect = conflict_error
        self.mock_database.get_container_client.return_value = self.mock_container
        
        # Mock container properties
        self.mock_container.read.return_value = {
            "partitionKey": {"paths": ["/id"]}
        }
        
        storage = CosmosDBStorage(self.config)
        await storage.initialize()
        
        # Verify fallback to get existing container
        self.mock_database.get_container_client.assert_called_once_with("test_container")
        self.assertFalse(storage._compatability_mode_partition_key)
    
    @patch('cosmos.CosmosClient')
    async def test_initialize_compatibility_mode_partition_key(self, mock_cosmos_client):
        """Test initialization with compatibility mode partition key"""
        mock_cosmos_client.return_value = self.mock_client
        self.mock_client.create_database_if_not_exists.return_value = self.mock_database
        
        # Mock conflict exception
        conflict_error = cosmos_exceptions.CosmosHttpResponseError(
            status_code=http_constants.StatusCodes.CONFLICT
        )
        self.mock_database.create_container.side_effect = conflict_error
        self.mock_database.get_container_client.return_value = self.mock_container
        
        # Mock container properties with old partition key
        self.mock_container.read.return_value = {
            "partitionKey": {"paths": ["/partitionKey"]}
        }
        
        storage = CosmosDBStorage(self.config)
        await storage.initialize()
        
        # Should enable compatibility mode
        self.assertTrue(storage._compatability_mode_partition_key)
    
    def test_get_partition_key_normal_mode(self):
        """Test partition key generation in normal mode"""
        with patch('cosmos.CosmosClient'):
            storage = CosmosDBStorage(self.config)
            storage._compatability_mode_partition_key = False
            
            result = storage._get_partition_key("test_key")
            self.assertEqual(result, "test_key")
    
    def test_get_partition_key_compatibility_mode(self):
        """Test partition key generation in compatibility mode"""
        with patch('cosmos.CosmosClient'):
            storage = CosmosDBStorage(self.config)
            storage._compatability_mode_partition_key = True
            
            result = storage._get_partition_key("test_key")
            self.assertEqual(result, "")


if __name__ == '__main__':
    # Run the tests
    unittest.main()
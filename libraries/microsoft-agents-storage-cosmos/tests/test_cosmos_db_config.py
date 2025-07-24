import json
import pytest

from microsoft.agents.storage.cosmos import CosmosDBStorageConfig

# thank you AI, again


@pytest.fixture()
def valid_config():
    """Fixture providing a valid CosmosDBStorageConfig for tests"""
    return CosmosDBStorageConfig(
        cosmos_db_endpoint="https://localhost:8081",
        auth_key=(
            "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGG"
            "yPMbIZnqyMsEcaGQy67XIw/Jw=="
        ),
        database_id="test-db",
        container_id="bot-storage",
    )


@pytest.fixture()
def minimal_config():
    """Fixture providing a minimal CosmosDBStorageConfig for tests"""
    return CosmosDBStorageConfig()


@pytest.fixture()
def config_with_options():
    """Fixture providing a CosmosDBStorageConfig with all options for tests"""
    return CosmosDBStorageConfig(
        cosmos_db_endpoint="https://test.documents.azure.com:443/",
        auth_key="test_key",
        database_id="test_db",
        container_id="test_container",
        cosmos_client_options={"connection_policy": "test"},
        container_throughput=800,
        key_suffix="_test",
        compatibility_mode=False,
    )


class TestCosmosDBStorageConfig:

    def test_constructor_with_parameters(self):
        """Test creating config with direct parameters"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
            container_throughput=800,
            key_suffix="_test",
            compatibility_mode=False,
        )

        assert config.cosmos_db_endpoint == "https://test.documents.azure.com:443/"
        assert config.auth_key == "test_key"
        assert config.database_id == "test_db"
        assert config.container_id == "test_container"
        assert config.container_throughput == 800
        assert config.key_suffix == "_test"
        assert config.compatibility_mode is False
        assert config.cosmos_client_options == {}
        assert config.credential is None

    def test_constructor_with_defaults(self):
        """Test creating config with default values"""
        config = CosmosDBStorageConfig()

        assert config.cosmos_db_endpoint == ""
        assert config.auth_key == ""
        assert config.database_id == ""
        assert config.container_id == ""
        assert config.container_throughput == 400  # Default value
        assert config.key_suffix == ""
        assert config.compatibility_mode is False
        assert config.cosmos_client_options == {}
        assert config.credential is None

    def test_from_file(self, tmp_path):
        """Test creating config from JSON file"""
        config_file_path = tmp_path / "cosmos_config.json"

        config_data = {
            "cosmos_db_endpoint": "https://localhost:8081",
            "auth_key": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
            "database_id": "test-db",
            "container_id": "bot-storage",
            "container_throughput": 600,
            "key_suffix": "_file",
            "compatibility_mode": True,
            "cosmos_client_options": {"connection_policy": "test"},
        }

        with open(config_file_path, "w") as f:
            json.dump(config_data, f)

        config = CosmosDBStorageConfig(filename=str(config_file_path))

        assert config.cosmos_db_endpoint == "https://localhost:8081"
        assert (
            config.auth_key
            == "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
        )
        assert config.database_id == "test-db"
        assert config.container_id == "bot-storage"
        assert config.container_throughput == 600
        assert config.key_suffix == "_file"
        assert config.compatibility_mode is True
        assert config.cosmos_client_options == {"connection_policy": "test"}

    def test_parameter_override_file(self, tmp_path):
        """Test that constructor parameters override file values"""
        config_file_path = tmp_path / "cosmos_config.json"

        with open(config_file_path, "w") as f:
            json.dump(
                {
                    "cosmos_db_endpoint": "https://file-endpoint.com",
                    "auth_key": "file_key",
                    "database_id": "file_db",
                },
                f,
            )

        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://param-endpoint.com",
            auth_key="param_key",
            filename=str(config_file_path),
        )

        # Parameters should override file values
        assert config.cosmos_db_endpoint == "https://param-endpoint.com"
        assert config.auth_key == "param_key"
        # File value should be used when parameter not provided
        assert config.database_id == "file_db"

    def test_validation_success(self):
        """Test successful validation with all required fields"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
        )

        # Should not raise any exception
        CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_missing_config(self):
        """Test validation with None config"""
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(None)

    def test_validation_missing_endpoint(self):
        """Test validation with missing cosmos_db_endpoint"""
        config = CosmosDBStorageConfig(
            auth_key="test_key", database_id="test_db", container_id="test_container"
        )
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_missing_auth_key(self):
        """Test validation with missing auth_key"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            database_id="test_db",
            container_id="test_container",
        )
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_missing_database_id(self):
        """Test validation with missing database_id"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            container_id="test_container",
        )
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_missing_container_id(self):
        """Test validation with missing container_id"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
        )
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_suffix_with_compatibility_mode(self):
        """Test validation fails when using suffix with compatibility mode"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
            key_suffix="_test",
            compatibility_mode=True,
        )
        with pytest.raises(ValueError):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_invalid_suffix_characters(self):
        """Test validation fails with invalid characters in suffix"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
            key_suffix="invalid/suffix\\with?bad#chars",
            compatibility_mode=False,
        )
        with pytest.raises(ValueError, match="Cannot use invalid Row Key characters"):
            CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_validation_valid_suffix(self):
        """Test validation succeeds with valid suffix"""
        config = CosmosDBStorageConfig(
            cosmos_db_endpoint="https://test.documents.azure.com:443/",
            auth_key="test_key",
            database_id="test_db",
            container_id="test_container",
            key_suffix="valid_suffix_123",
            compatibility_mode=False,
        )
        # Should not raise any exception
        CosmosDBStorageConfig.validate_cosmos_db_config(config)

    def test_cosmos_client_options(self):
        """Test cosmos_client_options handling"""
        options = {"connection_policy": "test", "consistency_level": "strong"}
        config = CosmosDBStorageConfig(cosmos_client_options=options)
        assert config.cosmos_client_options == options

    def test_credential_parameter(self):
        """Test credential parameter handling"""
        # Mock credential (in real usage this would be a TokenCredential instance)
        mock_credential = object()  # Placeholder for actual TokenCredential
        config = CosmosDBStorageConfig(credential=mock_credential)
        assert config.credential is mock_credential

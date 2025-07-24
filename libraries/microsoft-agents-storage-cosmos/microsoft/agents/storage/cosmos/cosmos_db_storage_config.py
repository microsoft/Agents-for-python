import json
from typing import Union

from azure.core.credentials import TokenCredential

from .key_ops import sanitize_key


class CosmosDBStorageConfig:
    """The class for partitioned CosmosDB configuration for the Azure Bot Framework."""

    def __init__(
        self,
        cosmos_db_endpoint: str = "",
        auth_key: str = "",
        database_id: str = "",
        container_id: str = "",
        cosmos_client_options: dict = None,
        container_throughput: int = 0,
        key_suffix: str = "",
        compatibility_mode: bool = False,
        url: str = "",
        credential: Union[TokenCredential, None] = None,
        **kwargs,
    ):
        """Create the Config object.

        :param cosmos_db_endpoint: The CosmosDB endpoint.
        :param auth_key: The authentication key for Cosmos DB.
        :param database_id: The database identifier for Cosmos DB instance.
        :param container_id: The container identifier.
        :param cosmos_client_options: The options for the CosmosClient. Currently only supports connection_policy and
            consistency_level
        :param container_throughput: The throughput set when creating the Container. Defaults to 400.
        :param key_suffix: The suffix to be added to every key. The keySuffix must contain only valid ComosDb
            key characters. (e.g. not: '\\', '?', '/', '#', '*')
        :param compatibility_mode: True if keys should be truncated in order to support previous CosmosDb
            max key length of 255.
        :param url: The URL to the CosmosDB resource.
        :param credential: The TokenCredential to use for authentication.
        :return CosmosDBConfig:
        """
        config_file: str = kwargs.get("filename", "")
        if config_file:
            kwargs = json.load(open(config_file))
        self.cosmos_db_endpoint: str = cosmos_db_endpoint or kwargs.get(
            "cosmos_db_endpoint", ""
        )
        self.auth_key: str = auth_key or kwargs.get("auth_key", "")
        self.database_id: str = database_id or kwargs.get("database_id", "")
        self.container_id: str = container_id or kwargs.get("container_id", "")
        self.cosmos_client_options: dict = cosmos_client_options or kwargs.get(
            "cosmos_client_options", {}
        )
        self.container_throughput: int = container_throughput or kwargs.get(
            "container_throughput", 400
        )
        self.key_suffix: str = key_suffix or kwargs.get("key_suffix", "")
        self.compatibility_mode: bool = compatibility_mode or kwargs.get(
            "compatibility_mode", False
        )
        self.url = url or kwargs.get("url", "")
        self.credential: Union[TokenCredential, None] = credential

    @staticmethod
    def validate_cosmos_db_config(config: "CosmosDBStorageConfig") -> None:
        """Validate the CosmosDBConfig object.

        This is used prior to the creation of the CosmosDBStorage object."""
        if not config:
            raise ValueError("CosmosDBStorage: CosmosDBConfig is required.")
        if not config.cosmos_db_endpoint:
            raise ValueError("CosmosDBStorage: cosmos_db_endpoint is required.")
        if not config.auth_key:
            raise ValueError("CosmosDBStorage: auth_key is required.")
        if not config.database_id:
            raise ValueError("CosmosDBStorage: database_id is required.")
        if not config.container_id:
            raise ValueError("CosmosDBStorage: container_id is required.")

        CosmosDBStorageConfig._validate_suffix(config)

    @staticmethod
    def _validate_suffix(config: "CosmosDBStorageConfig") -> None:
        if config.key_suffix:
            if config.compatibility_mode:
                raise ValueError(
                    "compatibilityMode cannot be true while using a keySuffix."
                )
            suffix_escaped: str = sanitize_key(config.key_suffix)
            if suffix_escaped != config.key_suffix:
                raise ValueError(
                    f"Cannot use invalid Row Key characters: {config.key_suffix} in keySuffix."
                )

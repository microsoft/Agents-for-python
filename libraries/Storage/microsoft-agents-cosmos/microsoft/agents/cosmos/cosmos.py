# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar
from threading import Lock
import json

from hashlib import sha256

from azure.cosmos import (
    documents,
    http_constants,
    CosmosClient,
    DatabaseProxy,
    ContainerProxy,
    CosmosDict,
)
import azure.cosmos.exceptions as cosmos_exceptions

from microsoft.agents.storage._type_aliases import JSON
from microsoft.agents.storage import Storage, StoreItem


StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class CosmosDBConfig:
    """The class for partitioned CosmosDB configuration for the Azure Bot Framework."""

    def __init__(
        self,
        cosmos_db_endpoint: str = "",
        auth_key: str = "",
        database_id: str = "",
        container_id: str = "",
        cosmos_client_options: dict = None,
        container_throughput: int = 400,
        key_suffix: str = "",
        compatibility_mode: bool = False,
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
        :return CosmosDBConfig:
        """
        config_file = kwargs.get("filename", "")
        if config_file:
            kwargs = json.load(open(config_file))
        self.cosmos_db_endpoint: str = cosmos_db_endpoint or kwargs.get(
            "cosmos_db_endpoint"
        )
        self.auth_key: str = auth_key or kwargs.get("auth_key")
        self.database_id: str = database_id or kwargs.get("database_id")
        self.container_id: str = container_id or kwargs.get("container_id")
        self.cosmos_client_options: dict = cosmos_client_options or kwargs.get(
            "cosmos_client_options", {}
        )
        self.container_throughput: int = container_throughput or kwargs.get(
            "container_throughput"
        )
        self.key_suffix: str = key_suffix or kwargs.get("key_suffix")
        self.compatibility_mode: bool = compatibility_mode or kwargs.get(
            "compatibility_mode"
        )


class CosmosDBKeyEscape:

    @staticmethod
    def sanitize_key(
        key: str, key_suffix: str = "", compatibility_mode: bool = True
    ) -> str:
        """Return the sanitized key.

        Replace characters that are not allowed in keys in Cosmos.

        :param key: The provided key to be escaped.
        :param key_suffix: The string to add a the end of all RowKeys.
        :param compatibility_mode: True if keys should be truncated in order to support previous CosmosDb
            max key length of 255.  This behavior can be overridden by setting
            cosmosdb_config.compatibility_mode to False.
        :return str:
        """
        # forbidden characters
        bad_chars: list[str] = ["\\", "?", "/", "#", "\t", "\n", "\r", "*"]

        # replace those with with '*' and the
        # Unicode code point of the character and return the new string
        key = "".join(map(lambda x: "*" + str(ord(x)) if x in bad_chars else x, key))
        return CosmosDBKeyEscape.truncate_key(f"{key}{key_suffix}", compatibility_mode)

    @staticmethod
    def truncate_key(key: str, compatibility_mode: bool = True) -> str:
        max_key_len: int = 255

        if not compatibility_mode:
            return key

        if len(key) > max_key_len:
            aux_hash = sha256(key.encode("utf-8"))
            aux_hex = aux_hash.hexdigest()

            key = key[0 : max_key_len - len(aux_hex)] + aux_hex

        return key


class CosmosDBStorage(Storage):
    """A CosmosDB based storage provider using partitioning for a bot."""

    def __init__(self, config: CosmosDBConfig):
        """Create the storage object.

        :param config:
        """
        super().__init__()
        self.config: CosmosDBConfig = config
        self.client: CosmosClient = None
        self.database: DatabaseProxy = None
        self.container: ContainerProxy = None
        self.compatability_mode_partition_key: bool = False
        # Lock used for synchronizing container creation
        self._lock: Lock = Lock()

        if config.key_suffix:
            if config.compatibility_mode:
                raise Exception(
                    "compatibilityMode cannot be true while using a keySuffix."
                )
            suffix_escaped: str = CosmosDBKeyEscape.sanitize_key(config.key_suffix)
            if suffix_escaped != config.key_suffix:
                raise Exception(
                    f"Cannot use invalid Row Key characters: {config.key_suffix} in keySuffix."
                )

    async def read(
        self, keys: list[str], *, target_cls: StoreItemT = None, **kwargs
    ) -> dict[str, StoreItemT]:
        """Read storeitems from storage.

        :param keys:
        :return dict:
        """
        if not keys:
            raise ValueError("CosmosDBStorage.read(): keys cannot be None or empty")

        await self.initialize()

        result: dict[str, StoreItemT] = {}
        for key in keys:
            try:
                escaped_key: str = CosmosDBKeyEscape.sanitize_key(
                    key, self.config.key_suffix, self.config.compatibility_mode
                )
                read_item_response: CosmosDict = self.container.read_item(
                    escaped_key, self._get_partition_key(escaped_key)
                )
                doc: JSON = read_item_response.get("document")
                result[read_item_response["realId"]] = (
                    target_cls.from_json_to_store_item(doc)
                )

            # When an item is not found a CosmosException is thrown, but we want to
            # return an empty collection
            except cosmos_exceptions.CosmosResourceNotFoundError:
                continue
            except Exception as err:
                raise err
        return result

    async def write(self, changes: dict[str, StoreItem]):
        """Save store items to storage.

        :param changes:
        :return:
        """
        if not changes:
            raise Exception("Changes are required when writing")

        await self.initialize()

        for key, item in changes.items():
            doc = {
                "id": CosmosDBKeyEscape.sanitize_key(
                    key, self.config.key_suffix, self.config.compatibility_mode
                ),
                "realId": key,
                "document": item.store_item_to_json(),
            }

            try:
                self.container.upsert_item(body=doc)
            except Exception as err:
                raise err

    async def delete(self, keys: list[str]):
        """Remove store items from storage.

        :param keys:
        :return:
        """
        await self.initialize()

        for key in keys:
            escaped_key: str = CosmosDBKeyEscape.sanitize_key(
                key, self.config.key_suffix, self.config.compatibility_mode
            )
            try:
                self.container.delete_item(
                    escaped_key,
                    self._get_partition_key(escaped_key),
                )
            except cosmos_exceptions.CosmosResourceNotFoundError:
                continue
            except Exception as err:
                raise err

    async def initialize(self):
        if not self.container:
            if not self.client:
                connection_policy = self.config.cosmos_client_options.get(
                    "connection_policy", documents.ConnectionPolicy()
                )

                # kwargs 'connection_verify' is to handle CosmosClient overwriting the
                # ConnectionPolicy.DisableSSLVerification value.
                self.client = CosmosClient(
                    self.config.cosmos_db_endpoint,
                    self.config.auth_key,
                    self.config.cosmos_client_options.get("consistency_level", None),
                    **{
                        "connection_policy": connection_policy,
                        "connection_verify": not connection_policy.DisableSSLVerification,
                    },
                )

            if not self.database:
                with self._lock:
                    if not self.database:
                        self.database = self.client.create_database_if_not_exists(
                            self.config.database_id
                        )

            self._get_or_create_container()

    def _get_or_create_container(self):

        if not self.container:
            with self._lock:
                partition_key = {
                    "paths": ["/id"],
                    "kind": documents.PartitionKind.Hash,
                }
                try:
                    self.container = self.database.create_container(
                        self.config.container_id,
                        partition_key,
                        offer_throughput=self.config.container_throughput,
                    )
                except cosmos_exceptions.CosmosHttpResponseError as err:
                    if err.status_code == http_constants.StatusCodes.CONFLICT:
                        self.container = self.database.get_container_client(
                            self.config.container_id
                        )
                        properties = self.container.read()
                        if "partitionKey" not in properties:
                            self.compatability_mode_partition_key = True
                        else:
                            paths = properties["partitionKey"]["paths"]
                            if "/partitionKey" in paths:
                                self.compatability_mode_partition_key = True
                            elif "/id" not in paths:
                                raise Exception(
                                    f"Custom Partition Key Paths are not supported. {self.config.container_id} "
                                    "has a custom Partition Key Path of {paths[0]}."
                                )

                    else:
                        raise err

    def _get_partition_key(self, key: str) -> str:
        return "" if self.compatability_mode_partition_key else key

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar, Union
from threading import Lock

from azure.cosmos import (
    documents,
    http_constants,
    CosmosDict,
)
from azure.cosmos.aio import (
    ContainerProxy,
    CosmosClient,
    DatabaseProxy,
)
import azure.cosmos.exceptions as cosmos_exceptions
from azure.cosmos.partition_key import NonePartitionKeyValue

from microsoft.agents.hosting.core.storage import AsyncStorageBase, StoreItem
from microsoft.agents.hosting.core.storage._type_aliases import JSON
from microsoft.agents.hosting.core.storage.error_handling import ignore_error

from .cosmos_db_storage_config import CosmosDBStorageConfig
from .key_ops import sanitize_key

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

cosmos_resource_not_found = lambda err: isinstance(
    err, cosmos_exceptions.CosmosResourceNotFoundError
)


class CosmosDBStorage(AsyncStorageBase):
    """A CosmosDB based storage provider using partitioning"""

    def __init__(self, config: CosmosDBStorageConfig):
        """Create the storage object.

        :param config:
        """
        super().__init__()

        CosmosDBStorageConfig.validate_cosmos_db_config(config)

        self._config: CosmosDBStorageConfig = config
        self._client: CosmosClient = self._create_client()
        self._database: DatabaseProxy = None
        self._container: ContainerProxy = None
        self._compatability_mode_partition_key: bool = False
        # Lock used for synchronizing container creation
        self._lock: Lock = Lock()

    def _create_client(self) -> CosmosClient:
        if self._config.url:
            if not self._config.credential:
                raise ValueError(
                    "CosmosDBStorage: Credential is required when using a custom service URL."
                )
            return CosmosClient(
                account_url=self._config.url, credential=self._config.credential
            )

        connection_policy = self._config.cosmos_client_options.get(
            "connection_policy", documents.ConnectionPolicy()
        )

        # kwargs 'connection_verify' is to handle CosmosClient overwriting the
        # ConnectionPolicy.DisableSSLVerification value.
        return CosmosClient(
            self._config.cosmos_db_endpoint,
            self._config.auth_key,
            consistency_level=self._config.cosmos_client_options.get(
                "consistency_level", None
            ),
            **{
                "connection_policy": connection_policy,
                "connection_verify": not connection_policy.DisableSSLVerification,
            },
        )

    def _sanitize(self, key: str) -> str:
        return sanitize_key(
            key, self._config.key_suffix, self._config.compatibility_mode
        )

    async def _read_item(
        self, key: str, *, target_cls: StoreItemT = None, **kwargs
    ) -> tuple[Union[str, None], Union[StoreItemT, None]]:

        if key == "":
            raise ValueError("CosmosDBStorage: Key cannot be empty.")

        escaped_key: str = self._sanitize(key)
        read_item_response: CosmosDict = await ignore_error(
            self._container.read_item(
                escaped_key, self._get_partition_key(escaped_key)
            ),
            cosmos_resource_not_found,
        )
        if read_item_response is None:
            return None, None

        doc: JSON = read_item_response.get("document")
        return read_item_response["realId"], target_cls.from_json_to_store_item(doc)

    async def _write_item(self, key: str, item: StoreItem) -> None:
        if key == "":
            raise ValueError("CosmosDBStorage: Key cannot be empty.")

        escaped_key: str = self._sanitize(key)

        doc = {
            "id": escaped_key,
            "realId": key,  # to retrieve the raw key later
            "document": item.store_item_to_json(),
        }
        await self._container.upsert_item(body=doc)

    async def _delete_item(self, key: str) -> None:
        if key == "":
            raise ValueError("CosmosDBStorage: Key cannot be empty.")

        escaped_key: str = self._sanitize(key)

        await ignore_error(
            self._container.delete_item(
                escaped_key, self._get_partition_key(escaped_key)
            ),
            cosmos_resource_not_found,
        )

    async def _create_container(self) -> None:
        partition_key = {
            "paths": ["/id"],
            "kind": documents.PartitionKind.Hash,
        }
        try:
            self._container = await self._database.create_container(
                self._config.container_id,
                partition_key,
                offer_throughput=self._config.container_throughput,
            )
        except cosmos_exceptions.CosmosHttpResponseError as err:
            if err.status_code == http_constants.StatusCodes.CONFLICT:
                self._container = self._database.get_container_client(
                    self._config.container_id
                )
                properties = await self._container.read()
                # if "partitionKey" not in properties:
                #     self._compatability_mode_partition_key = True
                # else:
                # containers created had no partition key, so the default was "/_partitionKey"
                paths = properties["partitionKey"]["paths"]
                if "/_partitionKey" in paths:
                    self._compatability_mode_partition_key = True
                elif "/id" not in paths:
                    raise Exception(
                        f"Custom Partition Key Paths are not supported. {self._config.container_id} "
                        "has a custom Partition Key Path of {paths[0]}."
                    )
            else:
                raise err

    async def initialize(self) -> None:
        if not self._container:
            with self._lock:
                # in case another thread attempted to initialize just before acquiring the lock
                if self._container:
                    return

                if not self._database:
                    self._database = await self._client.create_database_if_not_exists(
                        self._config.database_id
                    )

                await self._create_container()

    def _get_partition_key(self, key: str):
        return NonePartitionKeyValue if self._compatability_mode_partition_key else key

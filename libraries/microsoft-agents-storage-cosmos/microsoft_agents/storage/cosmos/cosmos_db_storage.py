# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, TypeVar, cast
import asyncio

from azure.cosmos import (
    documents,
    CosmosDict,
)
from azure.core import MatchConditions
from azure.cosmos.aio import (
    ContainerProxy,
    CosmosClient,
    DatabaseProxy,
)
import azure.cosmos.exceptions as cosmos_exceptions
from azure.cosmos.partition_key import NonePartitionKeyValue

from microsoft_agents.hosting.core.storage import (
    AsyncStorageBaseV2,
    AsyncStorageBase,
    StoreItem,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageOperationStatus,
    StorageReadResult,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
)
from microsoft_agents.hosting.core.storage._type_aliases import JSON
from microsoft_agents.hosting.core.storage.error_handling import ignore_error
from microsoft_agents.storage.cosmos.errors import storage_errors

from .cosmos_db_storage_config import CosmosDBStorageConfig
from .key_ops import sanitize_key

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

cosmos_resource_not_found = lambda err: isinstance(
    err, cosmos_exceptions.CosmosResourceNotFoundError
)


class _CosmosStorageBackend:
    """Own Cosmos DB lifecycle and version-neutral document operations."""

    def __init__(self, config: CosmosDBStorageConfig) -> None:
        CosmosDBStorageConfig.validate_cosmos_db_config(config)
        self._config = config
        self._client = self._create_client()
        self._database: DatabaseProxy | None = None
        self._container: ContainerProxy | None = None
        self._compatability_mode_partition_key = False
        self._lock = asyncio.Lock()

    def _create_client(self) -> CosmosClient:
        if self._config.url:
            if not self._config.credential:
                raise ValueError(
                    storage_errors.InvalidConfiguration.format(
                        "Credential is required when using a custom service URL"
                    )
                )
            return CosmosClient(
                url=self._config.url, credential=self._config.credential
            )
        connection_policy = self._config.cosmos_client_options.get(
            "connection_policy", documents.ConnectionPolicy()
        )
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

    def _get_partition_key(self, key: str):
        return NonePartitionKeyValue if self._compatability_mode_partition_key else key

    def _document(self, key: str, content: JSON) -> CosmosDict:
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))
        return {
            "id": self._sanitize(key),
            "realId": key,
            "document": content,
        }

    async def read(self, key: str, **kwargs: Any) -> CosmosDict:
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))
        escaped_key = self._sanitize(key)
        return await self._container.read_item(
            escaped_key, self._get_partition_key(escaped_key), **kwargs
        )

    async def try_read(self, key: str) -> CosmosDict | None:
        try:
            return await self.read(key)
        except Exception as error:  # noqa: BLE001
            if _status_code(error) == 404:
                return None
            raise

    async def create(self, key: str, content: JSON) -> CosmosDict:
        return await self._container.create_item(body=self._document(key, content))

    async def upsert(self, key: str, content: JSON) -> CosmosDict:
        return await self._container.upsert_item(body=self._document(key, content))

    async def replace(
        self,
        key: str,
        content: JSON,
        *,
        etag: str | None = None,
        match_condition: MatchConditions | None = None,
    ) -> CosmosDict:
        escaped_key = self._sanitize(key)
        replace_options: dict[str, Any] = {
            "item": escaped_key,
            "body": self._document(key, content),
        }
        if etag is not None:
            replace_options["etag"] = etag
        if match_condition is not None:
            replace_options["match_condition"] = match_condition
        return await self._container.replace_item(**replace_options)

    async def delete(
        self,
        key: str,
        *,
        etag: str | None = None,
        match_condition: MatchConditions | None = None,
    ) -> None:
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))
        escaped_key = self._sanitize(key)
        delete_options: dict[str, Any] = {}
        if etag is not None:
            delete_options["etag"] = etag
        if match_condition is not None:
            delete_options["match_condition"] = match_condition
        await self._container.delete_item(
            escaped_key,
            self._get_partition_key(escaped_key),
            **delete_options,
        )

    async def _create_container(self) -> None:
        partition_key = {"paths": ["/id"], "kind": documents.PartitionKind.Hash}
        try:
            kwargs = {}
            if self._config.container_throughput:
                kwargs["offer_throughput"] = self._config.container_throughput
            self._container = await self._database.create_container(
                self._config.container_id, partition_key, **kwargs
            )
        except Exception:
            self._container = self._database.get_container_client(
                self._config.container_id
            )
            properties = await self._container.read()
            paths = properties["partitionKey"]["paths"]
            if "/_partitionKey" in paths:
                self._compatability_mode_partition_key = True
            elif "/id" not in paths:
                raise Exception(
                    storage_errors.InvalidConfiguration.format(
                        "Custom Partition Key Paths are not supported. "
                        f"{self._config.container_id} has a custom Partition "
                        f"Key Path of {paths[0]}."
                    )
                )

    async def initialize(self) -> None:
        if not self._container:
            async with self._lock:
                if self._container:
                    return
                if not self._database:
                    self._database = await self._client.create_database_if_not_exists(
                        self._config.database_id
                    )
                await self._create_container()

    async def close(self) -> None:
        await self._client.close()


def _status_code(error: Exception) -> int | None:
    return getattr(error, "status_code", None)


class CosmosDBStorage(AsyncStorageBase):
    """Legacy Cosmos DB storage adapter."""

    def __init__(self, config: CosmosDBStorageConfig):
        """Create the storage object."""
        self._config = config
        self._backend = _CosmosStorageBackend(config)

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Read an item from the storage.

        :param key: The key of the item to read.
        :param target_cls: The type of the item to read.
        :return: A tuple containing the real key and the item, or (None, None) if not found.
        :raises ValueError: If the key is empty.
        """

        read_item_response: CosmosDict | None = await ignore_error(
            self._backend.read(key, **kwargs),
            cosmos_resource_not_found,
        )
        if read_item_response is None:
            return None, None

        doc: JSON | None = read_item_response.get("document")
        if doc is None:
            return read_item_response["realId"], None
        return read_item_response["realId"], cast(
            StoreItemT, target_cls.from_json_to_store_item(doc)
        )

    async def _write_item(self, key: str, item: StoreItem) -> None:
        """Write an item to the storage.

        :param key: The key of the item to write.
        :param item: The item to write.
        :raises ValueError: If the key is empty.
        """
        await self._backend.upsert(key, item.store_item_to_json())

    async def _delete_item(self, key: str) -> None:
        """Delete an item from the storage.

        :param key: The key of the item to delete.
        :raises ValueError: If the key is empty.
        """
        await ignore_error(
            self._backend.delete(key),
            cosmos_resource_not_found,
        )

    async def initialize(self) -> None:
        await self._backend.initialize()

    async def close(self) -> None:
        """Close the Azure client owned by this adapter."""
        await self._backend.close()


class CosmosDBStorageV2(AsyncStorageBaseV2):
    """Cosmos DB Storage V2 adapter with per-key results."""

    def __init__(self, config: CosmosDBStorageConfig):
        self._config = config
        self._backend = _CosmosStorageBackend(config)

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs: Any
    ) -> StorageReadResult[StoreItemT]:
        try:
            document = await self._backend.read(key, **kwargs)
            return cast(
                StorageReadResult[StoreItemT],
                StorageReadResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    value=cast(
                        StoreItemT,
                        target_cls.from_json_to_store_item(document["document"]),
                    ),
                    version=document.get("_etag"),
                ),
            )
        except Exception as error:  # noqa: BLE001
            if _status_code(error) == 404:
                return cast(
                    StorageReadResult[StoreItemT],
                    StorageReadResult(key=key, status=StorageOperationStatus.NOT_FOUND),
                )
            raise

    async def _write_item(
        self,
        key: str,
        value: StoreItem,
        options: StorageWriteOptions,
    ) -> StorageWriteResult:
        if (
            options.mode == StorageWriteMode.CREATE_ONLY
            and options.expected_version is not None
        ):
            current = await self._backend.try_read(key)
            current_version = current.get("_etag") if current else None
            return StorageWriteResult(
                key=key,
                status=(
                    StorageOperationStatus.CONFLICT
                    if current is not None
                    else StorageOperationStatus.CONDITION_NOT_MET
                ),
                version=current_version,
            )
        content = value.store_item_to_json()
        try:
            if options.mode == StorageWriteMode.CREATE_ONLY:
                response = await self._backend.create(key, content)
            elif (
                options.mode == StorageWriteMode.REPLACE
                or options.expected_version is not None
            ):
                response = await self._backend.replace(
                    key,
                    content,
                    etag=options.expected_version,
                    match_condition=(
                        MatchConditions.IfNotModified
                        if options.expected_version is not None
                        else None
                    ),
                )
            else:
                response = await self._backend.upsert(key, content)
            return StorageWriteResult(
                key=key,
                status=StorageOperationStatus.SUCCEEDED,
                version=response.get("_etag"),
            )
        except Exception as error:  # noqa: BLE001
            status_code = _status_code(error)
            if options.mode == StorageWriteMode.CREATE_ONLY and status_code == 409:
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONFLICT,
                    version=(await self._backend.try_read(key) or {}).get("_etag"),
                )
            if status_code == 404:
                return StorageWriteResult(
                    key=key,
                    status=(
                        StorageOperationStatus.CONDITION_NOT_MET
                        if options.expected_version is not None
                        else StorageOperationStatus.NOT_FOUND
                    ),
                )
            if status_code == 412:
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=(await self._backend.try_read(key) or {}).get("_etag"),
                )
            raise

    async def _delete_item(
        self,
        key: str,
        options: StorageDeleteOptions,
    ) -> StorageDeleteResult:
        try:
            await self._backend.delete(
                key,
                etag=options.expected_version,
                match_condition=(
                    MatchConditions.IfNotModified
                    if options.expected_version is not None
                    else None
                ),
            )
            return StorageDeleteResult(
                key=key,
                status=StorageOperationStatus.SUCCEEDED,
                version=options.expected_version,
            )
        except Exception as error:  # noqa: BLE001
            status_code = _status_code(error)
            if status_code == 404:
                return StorageDeleteResult(
                    key=key,
                    status=(
                        StorageOperationStatus.CONDITION_NOT_MET
                        if options.expected_version is not None
                        else StorageOperationStatus.NOT_FOUND
                    ),
                )
            if status_code == 412:
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=(await self._backend.try_read(key) or {}).get("_etag"),
                )
            raise

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        await self._backend.initialize()

    async def close(self) -> None:
        """Close the Azure client owned by this adapter."""
        await self._backend.close()

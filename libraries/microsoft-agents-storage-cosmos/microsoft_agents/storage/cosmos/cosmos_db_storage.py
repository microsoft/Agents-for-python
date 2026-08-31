# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Generic, Literal, TypeVar, cast, overload
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
    AsyncStorageBase,
    StoreItem,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageDeleteResults,
    StorageOperationStatus,
    StorageReadResult,
    StorageReadResults,
    StorageV2,
    StorageVersion,
    StorageVersionT,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
    StorageWriteResults,
    is_store_item,
)
from microsoft_agents.hosting.core.storage._type_aliases import JSON
from microsoft_agents.hosting.core.storage.error_handling import ignore_error
from microsoft_agents.hosting.core.storage.storage_compatibility import (
    validate_expected_version,
    validate_storage_v2_changes,
    validate_storage_v2_keys,
    validate_write_mode,
)
from microsoft_agents.hosting.core.storage.telemetry import spans
from microsoft_agents.storage.cosmos.errors import storage_errors

from .cosmos_db_storage_config import CosmosDBStorageConfig
from .key_ops import sanitize_key

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

cosmos_resource_not_found = lambda err: isinstance(
    err, cosmos_exceptions.CosmosResourceNotFoundError
)


class CosmosDBStorage(AsyncStorageBase, StorageV2, Generic[StorageVersionT]):
    """A CosmosDB based storage provider using partitioning"""

    def __init__(self, config: CosmosDBStorageConfig[StorageVersionT]):
        """Create the storage object.

        :param config:
        """
        super().__init__()

        CosmosDBStorageConfig.validate_cosmos_db_config(config)

        self._config: CosmosDBStorageConfig[StorageVersionT] = config
        if config.storage_version not in (StorageVersion.V1, StorageVersion.V2):
            raise ValueError(
                f'Storage version "{config.storage_version}" is not supported.'
            )
        self.storage_version = StorageVersion(config.storage_version)
        self._client: CosmosClient = self._create_client()
        self._database: DatabaseProxy | None = None
        self._container: ContainerProxy | None = None
        self._compatability_mode_partition_key: bool = False
        # Lock used for synchronizing container creation
        self._lock: asyncio.Lock = asyncio.Lock()

    @overload
    async def read(
        self: "CosmosDBStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> dict[str, StoreItemT]: ...

    @overload
    async def read(
        self: "CosmosDBStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> StorageReadResults[StoreItemT]: ...

    @overload
    async def read(
        self: "CosmosDBStorage[StorageVersion]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> dict[str, StoreItemT] | StorageReadResults[StoreItemT]: ...

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> dict[str, StoreItemT] | StorageReadResults[StoreItemT]:
        """Read items using the selected storage contract."""
        if self.storage_version == StorageVersion.V1:
            return await super().read(keys, target_cls=target_cls, **kwargs)
        with spans.StorageRead(len(keys) if isinstance(keys, list) else 0):
            return await self._read_v2(keys, target_cls=target_cls)

    @overload
    async def write(
        self: "CosmosDBStorage[Literal[StorageVersion.V1]]",
        changes: dict[str, StoreItem],
        options: None = None,
    ) -> None: ...

    @overload
    async def write(
        self: "CosmosDBStorage[Literal[StorageVersion.V2]]",
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults: ...

    @overload
    async def write(
        self: "CosmosDBStorage[StorageVersion]",
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> None | StorageWriteResults: ...

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> None | StorageWriteResults:
        """Write items using the selected storage contract."""
        if self.storage_version == StorageVersion.V1:
            if options is not None:
                raise ValueError("Storage write options require Storage V2.")
            return await super().write(changes)
        with spans.StorageWrite(len(changes) if isinstance(changes, dict) else 0):
            return await self._write_v2(changes, options)

    @overload
    async def delete(
        self: "CosmosDBStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        options: None = None,
    ) -> None: ...

    @overload
    async def delete(
        self: "CosmosDBStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults: ...

    @overload
    async def delete(
        self: "CosmosDBStorage[StorageVersion]",
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> None | StorageDeleteResults: ...

    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> None | StorageDeleteResults:
        """Delete items using the selected storage contract."""
        if self.storage_version == StorageVersion.V1:
            if options is not None:
                raise ValueError("Storage delete options require Storage V2.")
            return await super().delete(keys)
        with spans.StorageDelete(len(keys) if isinstance(keys, list) else 0):
            return await self._delete_v2(keys, options)

    def _create_client(self) -> CosmosClient:
        """Create a CosmosClient based on the configuration.

        :return: A CosmosClient instance.
        :raises ValueError: If the configuration is invalid.
        """
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
        """Sanitize the key for use in CosmosDB."""
        return sanitize_key(
            key, self._config.key_suffix, self._config.compatibility_mode
        )

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Read an item from the storage.

        :param key: The key of the item to read.
        :param target_cls: The type of the item to read.
        :return: A tuple containing the real key and the item, or (None, None) if not found.
        :raises ValueError: If the key is empty.
        """

        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))

        escaped_key: str = self._sanitize(key)
        read_item_response: CosmosDict | None = await ignore_error(
            self._container.read_item(
                escaped_key, self._get_partition_key(escaped_key)
            ),
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
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))

        escaped_key: str = self._sanitize(key)

        doc = {
            "id": escaped_key,
            "realId": key,  # to retrieve the raw key later
            "document": item.store_item_to_json(),
        }
        await self._container.upsert_item(body=doc)

    async def _delete_item(self, key: str) -> None:
        """Delete an item from the storage.

        :param key: The key of the item to delete.
        :raises ValueError: If the key is empty.
        """
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))

        escaped_key: str = self._sanitize(key)

        await ignore_error(
            self._container.delete_item(
                escaped_key, self._get_partition_key(escaped_key)
            ),
            cosmos_resource_not_found,
        )

    async def _read_v2(
        self, keys: list[str], *, target_cls: type[StoreItemT]
    ) -> StorageReadResults[StoreItemT]:
        validate_storage_v2_keys(keys)
        if not keys:
            return {}
        await self.initialize()

        async def read_one(key: str) -> StorageReadResult[StoreItemT]:
            try:
                document = await self._read_document(key)
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
                if self._status_code(error) == 404:
                    return cast(
                        StorageReadResult[StoreItemT],
                        StorageReadResult(
                            key=key, status=StorageOperationStatus.NOT_FOUND
                        ),
                    )
                else:
                    raise

        results = await asyncio.gather(*(read_one(key) for key in keys))
        return {result.key: result for result in results}

    async def _write_v2(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None,
    ) -> StorageWriteResults:
        validate_storage_v2_changes(changes)
        if not changes:
            return {}
        if any(not is_store_item(value) for value in changes.values()):
            raise ValueError("Storage V2 values must implement store_item_to_json().")
        write_options = options or StorageWriteOptions()
        validate_write_mode(write_options.mode)
        validate_expected_version(write_options.expected_version)
        await self.initialize()

        async def write_one(key: str, value: StoreItem) -> StorageWriteResult:
            current = await self._try_read_document(key)
            current_version = current.get("_etag") if current else None
            if (
                write_options.mode == StorageWriteMode.CREATE_ONLY
                and current is not None
            ):
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONFLICT,
                    version=current_version,
                )
            if write_options.mode == StorageWriteMode.REPLACE and current is None:
                return StorageWriteResult(
                    key=key, status=StorageOperationStatus.NOT_FOUND
                )
            if (
                write_options.expected_version is not None
                and write_options.expected_version != current_version
            ):
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=current_version,
                )

            escaped_key = self._sanitize(key)
            document = {
                "id": escaped_key,
                "realId": key,
                "document": value.store_item_to_json(),
            }
            try:
                if write_options.mode == StorageWriteMode.CREATE_ONLY:
                    response = await self._container.create_item(body=document)
                elif write_options.mode == StorageWriteMode.REPLACE:
                    response = await self._container.replace_item(
                        escaped_key,
                        document,
                        etag=current_version,
                        match_condition=MatchConditions.IfNotModified,
                    )
                elif write_options.expected_version is not None:
                    response = await self._container.upsert_item(
                        body=document,
                        etag=write_options.expected_version,
                        match_condition=MatchConditions.IfNotModified,
                    )
                else:
                    response = await self._container.upsert_item(body=document)
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=response.get("_etag"),
                )
            except Exception as error:  # noqa: BLE001
                status_code = self._status_code(error)
                if (
                    write_options.mode == StorageWriteMode.CREATE_ONLY
                    and status_code == 409
                ):
                    return StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONFLICT,
                        version=(await self._try_read_document(key) or {}).get("_etag"),
                    )
                if status_code == 404:
                    return StorageWriteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                if status_code == 412:
                    return StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=(await self._try_read_document(key) or {}).get("_etag"),
                    )
                raise

        results = await asyncio.gather(
            *(write_one(key, value) for key, value in changes.items())
        )
        return {result.key: result for result in results}

    async def _delete_v2(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None,
    ) -> StorageDeleteResults:
        validate_storage_v2_keys(keys)
        if not keys:
            return {}
        delete_options = options or StorageDeleteOptions()
        validate_expected_version(delete_options.expected_version)
        await self.initialize()

        async def delete_one(key: str) -> StorageDeleteResult:
            current = await self._try_read_document(key)
            if current is None:
                return StorageDeleteResult(
                    key=key, status=StorageOperationStatus.NOT_FOUND
                )
            current_version = current.get("_etag")
            if (
                delete_options.expected_version is not None
                and delete_options.expected_version != current_version
            ):
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=current_version,
                )
            escaped_key = self._sanitize(key)
            try:
                await self._container.delete_item(
                    escaped_key,
                    self._get_partition_key(escaped_key),
                    etag=current_version,
                    match_condition=MatchConditions.IfNotModified,
                )
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=current_version,
                )
            except Exception as error:  # noqa: BLE001
                status_code = self._status_code(error)
                if status_code == 404:
                    return StorageDeleteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                if status_code == 412:
                    return StorageDeleteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=(await self._try_read_document(key) or {}).get("_etag"),
                    )
                raise

        results = await asyncio.gather(*(delete_one(key) for key in keys))
        return {result.key: result for result in results}

    async def _read_document(self, key: str) -> CosmosDict:
        if key == "":
            raise ValueError(str(storage_errors.CosmosDbKeyCannotBeEmpty))
        escaped_key = self._sanitize(key)
        return await self._container.read_item(
            escaped_key, self._get_partition_key(escaped_key)
        )

    async def _try_read_document(self, key: str) -> CosmosDict | None:
        try:
            return await self._read_document(key)
        except Exception as error:  # noqa: BLE001
            if self._status_code(error) == 404:
                return None
            raise

    @staticmethod
    def _status_code(error: Exception) -> int | None:
        return getattr(error, "status_code", None)

    async def _create_container(self) -> None:
        """Create the container if it does not exist."""
        partition_key = {
            "paths": ["/id"],
            "kind": documents.PartitionKind.Hash,
        }
        try:
            kwargs = {}
            if self._config.container_throughput:
                kwargs["offer_throughput"] = self._config.container_throughput
            self._container = await self._database.create_container(
                self._config.container_id, partition_key, **kwargs
            )
        except Exception as err:
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
                    storage_errors.InvalidConfiguration.format(
                        f"Custom Partition Key Paths are not supported. {self._config.container_id} has a custom Partition Key Path of {paths[0]}."
                    )
                )

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        if not self._container:
            async with self._lock:
                # in case another async task attempted to initialize just before acquiring the lock
                if self._container:
                    return

                if not self._database:
                    self._database = await self._client.create_database_if_not_exists(
                        self._config.database_id
                    )

                await self._create_container()

    def _get_partition_key(self, key: str):
        """Get the partition key for the given key, considering compatibility mode.

        :param key: The key for which to get the partition key.
        :return: The partition key value.
        """
        return NonePartitionKeyValue if self._compatability_mode_partition_key else key

    async def _close(self) -> None:
        """Close the storage provider."""
        await self._client.close()

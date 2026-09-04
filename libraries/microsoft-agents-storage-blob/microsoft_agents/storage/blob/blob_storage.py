import asyncio
import json
from typing import Generic, Literal, TypeVar, cast, overload
from io import BytesIO

from azure.core import MatchConditions
from azure.storage.blob.aio import (
    ContainerClient,
    BlobServiceClient,
)

from microsoft_agents.hosting.core.storage import (
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
from microsoft_agents.hosting.core.storage.storage import AsyncStorageBase
from microsoft_agents.hosting.core.storage._type_aliases import JSON
from microsoft_agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)
from microsoft_agents.hosting.core.storage.storage_compatibility import (
    validate_expected_version,
    validate_storage_v2_changes,
    validate_storage_v2_keys,
    validate_write_mode,
)
from microsoft_agents.hosting.core.storage.telemetry import spans
from microsoft_agents.storage.blob.errors import blob_storage_errors

from .blob_storage_config import BlobStorageConfig

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class BlobStorage(AsyncStorageBase, StorageV2, Generic[StorageVersionT]):
    """A Blob Storage provider for storing StoreItem objects in Azure Blob Storage."""

    def __init__(self, config: BlobStorageConfig[StorageVersionT]):
        """Initialize the BlobStorage with the given configuration.

        :param config: BlobStorageConfig object containing the configuration for the blob storage.
        :raises ValueError: If the container name is not provided in the configuration.
        """

        if not config.container_name:
            raise ValueError(str(blob_storage_errors.BlobContainerNameRequired))

        self.config = config
        if config.storage_version not in (StorageVersion.V1, StorageVersion.V2):
            raise ValueError(
                f'Storage version "{config.storage_version}" is not supported.'
            )
        self.storage_version = StorageVersion(config.storage_version)

        self._blob_service_client: BlobServiceClient = self._create_client()
        self._container_client: ContainerClient = (
            self._blob_service_client.get_container_client(config.container_name)
        )
        self._initialized: bool = False

    @overload
    async def read(
        self: "BlobStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> dict[str, StoreItemT]: ...

    @overload
    async def read(
        self: "BlobStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> StorageReadResults[StoreItemT]: ...

    @overload
    async def read(
        self: "BlobStorage[StorageVersion]",
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
        self: "BlobStorage[Literal[StorageVersion.V1]]",
        changes: dict[str, StoreItem],
        options: None = None,
    ) -> None: ...

    @overload
    async def write(
        self: "BlobStorage[Literal[StorageVersion.V2]]",
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults: ...

    @overload
    async def write(
        self: "BlobStorage[StorageVersion]",
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
        self: "BlobStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        options: None = None,
    ) -> None: ...

    @overload
    async def delete(
        self: "BlobStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults: ...

    @overload
    async def delete(
        self: "BlobStorage[StorageVersion]",
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

    def _create_client(self) -> BlobServiceClient:
        """Creates a BlobServiceClient based on the provided configuration.
        :return: An instance of BlobServiceClient.
        :raises ValueError: If the configuration is invalid.
        """
        if self.config.url:  # connect with URL and credentials
            if not self.config.credential:
                raise ValueError(
                    blob_storage_errors.InvalidConfiguration.format(
                        "Credential is required when using a custom service URL"
                    )
                )
            return BlobServiceClient(
                account_url=self.config.url, credential=self.config.credential
            )

        else:  # connect with connection string
            return BlobServiceClient.from_connection_string(
                self.config.connection_string
            )

    async def initialize(self) -> None:
        """Initializes the storage container"""
        if not self._initialized:
            # This should only happen once - assuming this is a singleton.
            await ignore_error(
                self._container_client.create_container(), is_status_code_error(409)
            )
            self._initialized = True

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Reads an item from blob storage.

        :param key: The key of the item to read.
        :param target_cls: The type of the StoreItem to deserialize into.
        :return: A tuple containing the key and the deserialized StoreItem, or (None, None) if not found.
        """
        item = await ignore_error(
            self._container_client.download_blob(blob=key, timeout=5),
            is_status_code_error(404),
        )
        if not item:
            return None, None

        item_rep: bytes = await item.readall()
        item_JSON: JSON = json.loads(item_rep)
        try:
            return key, cast(StoreItemT, target_cls.from_json_to_store_item(item_JSON))
        except AttributeError as error:
            raise TypeError(
                f"BlobStorage.read_item(): could not deserialize blob item into {target_cls} class. Error: {error}"
            )

    async def _write_item(self, key: str, item: StoreItem) -> None:
        """Writes an item to blob storage.

        :param key: The key under which to store the item.
        :param item: The StoreItem to serialize and store.
        :raises ValueError: If the StoreItem serialization returns None.
        """
        item_JSON: JSON = item.store_item_to_json()
        if item_JSON is None:
            raise ValueError(
                "BlobStorage.write(): StoreItem serialization cannot return None"
            )
        item_rep_bytes = json.dumps(item_JSON).encode("utf-8")

        # getting the length is important for performance with large blobs
        await self._container_client.upload_blob(
            name=key,
            data=BytesIO(item_rep_bytes),
            overwrite=True,
            length=len(item_rep_bytes),
        )

    async def _delete_item(self, key: str) -> None:
        """Deletes an item from blob storage.

        :param key: The key of the item to delete.
        :raises ValueError: If the deletion fails for reasons other than the item not existing.
        """
        await ignore_error(
            self._container_client.delete_blob(blob=key), is_status_code_error(404)
        )

    async def _read_v2(
        self, keys: list[str], *, target_cls: type[StoreItemT]
    ) -> StorageReadResults[StoreItemT]:
        validate_storage_v2_keys(keys)
        if not keys:
            return {}
        await self.initialize()

        async def read_one(key: str) -> StorageReadResult[StoreItemT]:
            blob_client = self._container_client.get_blob_client(key)
            try:
                downloader = await blob_client.download_blob(timeout=5)
                raw = await downloader.readall()
                value = cast(
                    StoreItemT,
                    target_cls.from_json_to_store_item(json.loads(raw)),
                )
                return cast(
                    StorageReadResult[StoreItemT],
                    StorageReadResult(
                        key=key,
                        status=StorageOperationStatus.SUCCEEDED,
                        value=value,
                        version=self._etag_from(downloader.properties),
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
            blob_client = self._container_client.get_blob_client(key)
            current_version = await self._get_current_version(blob_client)
            if (
                write_options.mode == StorageWriteMode.CREATE_ONLY
                and current_version is not None
            ):
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONFLICT,
                    version=current_version,
                )
            if (
                write_options.mode == StorageWriteMode.REPLACE
                and current_version is None
            ):
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

            payload = json.dumps(value.store_item_to_json()).encode("utf-8")
            try:
                upload_options = {
                    "overwrite": write_options.mode != StorageWriteMode.CREATE_ONLY
                }
                condition_version = write_options.expected_version
                if write_options.mode == StorageWriteMode.REPLACE:
                    condition_version = current_version
                if condition_version is not None:
                    upload_options.update(
                        {
                            "etag": condition_version,
                            "match_condition": MatchConditions.IfNotModified,
                        }
                    )
                response = await blob_client.upload_blob(
                    BytesIO(payload), length=len(payload), **upload_options
                )
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=self._etag_from(response),
                )
            except Exception as error:  # noqa: BLE001
                status_code = self._status_code(error)
                if (
                    write_options.mode == StorageWriteMode.CREATE_ONLY
                    and status_code
                    in (
                        409,
                        412,
                    )
                ):
                    return StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONFLICT,
                        version=await self._get_current_version(blob_client),
                    )
                if status_code == 404:
                    return StorageWriteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                if status_code == 412:
                    return StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=await self._get_current_version(blob_client),
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
            blob_client = self._container_client.get_blob_client(key)
            current_version = await self._get_current_version(blob_client)
            if current_version is None:
                return StorageDeleteResult(
                    key=key, status=StorageOperationStatus.NOT_FOUND
                )
            if (
                delete_options.expected_version is not None
                and delete_options.expected_version != current_version
            ):
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=current_version,
                )
            try:
                await blob_client.delete_blob(
                    etag=current_version,
                    match_condition=MatchConditions.IfNotModified,
                )
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=current_version,
                )
            except Exception as error:  # noqa: BLE001
                if self._status_code(error) == 404:
                    return StorageDeleteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                if self._status_code(error) == 412:
                    return StorageDeleteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=await self._get_current_version(blob_client),
                    )
                raise

        results = await asyncio.gather(*(delete_one(key) for key in keys))
        return {result.key: result for result in results}

    async def _get_current_version(self, blob_client) -> str | None:
        try:
            return self._etag_from(await blob_client.get_blob_properties())
        except Exception as error:  # noqa: BLE001
            if self._status_code(error) == 404:
                return None
            raise

    @staticmethod
    def _etag_from(properties) -> str | None:
        if isinstance(properties, dict):
            return properties.get("etag")
        return getattr(properties, "etag", None)

    @staticmethod
    def _status_code(error: Exception) -> int | None:
        return getattr(error, "status_code", None)

    async def _close(self) -> None:
        """Cleans up the storage resources."""
        await self._container_client.close()
        await self._blob_service_client.close()

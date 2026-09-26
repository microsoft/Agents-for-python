import json
from dataclasses import dataclass
from typing import Any, TypeVar, cast
from io import BytesIO

from azure.core import MatchConditions
from azure.storage.blob.aio import (
    BlobServiceClient,
)

from microsoft_agents.hosting.core.storage import (
    StoreItem,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageOperationStatus,
    StorageReadResult,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
)
from microsoft_agents.hosting.core.storage.storage import (
    AsyncStorageBase,
    AsyncStorageBaseV2,
)
from microsoft_agents.hosting.core.storage._type_aliases import JSON
from microsoft_agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)
from microsoft_agents.storage.blob.errors import blob_storage_errors

from .blob_storage_config import BlobStorageConfig

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


@dataclass(frozen=True, slots=True)
class _BlobDocument:
    content: bytes
    version: str | None


class _BlobStorageBackend:
    """Own Azure Blob lifecycle and version-neutral blob operations."""

    def __init__(self, config: BlobStorageConfig) -> None:
        if not config.container_name:
            raise ValueError(str(blob_storage_errors.BlobContainerNameRequired))
        self._config = config
        self._blob_service_client = self._create_client()
        self._container_client = self._blob_service_client.get_container_client(
            config.container_name
        )
        self._initialized = False

    def _create_client(self) -> BlobServiceClient:
        if self._config.url:
            if not self._config.credential:
                raise ValueError(
                    blob_storage_errors.InvalidConfiguration.format(
                        "Credential is required when using a custom service URL"
                    )
                )
            return BlobServiceClient(
                account_url=self._config.url, credential=self._config.credential
            )
        return BlobServiceClient.from_connection_string(self._config.connection_string)

    async def initialize(self) -> None:
        if not self._initialized:
            await ignore_error(
                self._container_client.create_container(), is_status_code_error(409)
            )
            self._initialized = True

    async def read(self, key: str, **kwargs: Any) -> _BlobDocument | None:
        blob_client = self._container_client.get_blob_client(key)
        try:
            downloader = await blob_client.download_blob(**kwargs)
            return _BlobDocument(
                content=await downloader.readall(),
                version=_etag_from(downloader.properties),
            )
        except Exception as error:  # noqa: BLE001
            if _status_code(error) == 404:
                return None
            raise

    async def write(
        self,
        key: str,
        content: bytes,
        *,
        overwrite: bool,
        etag: str | None = None,
        match_condition: MatchConditions | None = None,
    ) -> str | None:
        upload_options: dict[str, Any] = {"overwrite": overwrite}
        if etag is not None:
            upload_options["etag"] = etag
        if match_condition is not None:
            upload_options["match_condition"] = match_condition
        response = await self._container_client.get_blob_client(key).upload_blob(
            BytesIO(content), length=len(content), **upload_options
        )
        return _etag_from(response)

    async def delete(
        self,
        key: str,
        *,
        etag: str | None = None,
        match_condition: MatchConditions | None = None,
    ) -> None:
        delete_options: dict[str, Any] = {}
        if etag is not None:
            delete_options["etag"] = etag
        if match_condition is not None:
            delete_options["match_condition"] = match_condition
        await self._container_client.get_blob_client(key).delete_blob(**delete_options)

    async def get_version(self, key: str) -> str | None:
        try:
            properties = await self._container_client.get_blob_client(
                key
            ).get_blob_properties()
            return _etag_from(properties)
        except Exception as error:  # noqa: BLE001
            if _status_code(error) == 404:
                return None
            raise

    async def close(self) -> None:
        await self._container_client.close()
        await self._blob_service_client.close()


def _etag_from(properties: Any) -> str | None:
    if isinstance(properties, dict):
        return properties.get("etag")
    return getattr(properties, "etag", None)


def _status_code(error: Exception) -> int | None:
    return getattr(error, "status_code", None)


class BlobStorage(AsyncStorageBase):
    """Legacy Azure Blob storage adapter."""

    def __init__(self, config: BlobStorageConfig):
        """Initialize the BlobStorage with the given configuration.

        :param config: BlobStorageConfig object containing the configuration for the blob storage.
        :raises ValueError: If the container name is not provided in the configuration.
        """

        self.config = config
        self._backend = _BlobStorageBackend(config)

    async def initialize(self) -> None:
        """Initializes the storage container"""
        await self._backend.initialize()

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Reads an item from blob storage.

        :param key: The key of the item to read.
        :param target_cls: The type of the StoreItem to deserialize into.
        :return: A tuple containing the key and the deserialized StoreItem, or (None, None) if not found.
        """
        read_options = {"timeout": 5, **kwargs}
        document = await self._backend.read(key, **read_options)
        if document is None:
            return None, None

        item_JSON: JSON = json.loads(document.content)
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

        await self._backend.write(key, item_rep_bytes, overwrite=True)

    async def _delete_item(self, key: str) -> None:
        """Deletes an item from blob storage.

        :param key: The key of the item to delete.
        :raises ValueError: If the deletion fails for reasons other than the item not existing.
        """
        try:
            await self._backend.delete(key)
        except Exception as error:  # noqa: BLE001
            if _status_code(error) != 404:
                raise

    async def close(self) -> None:
        """Close the Azure clients owned by this adapter."""
        await self._backend.close()


class BlobStorageV2(AsyncStorageBaseV2):
    """Azure Blob Storage V2 adapter with per-key results."""

    def __init__(self, config: BlobStorageConfig):
        self.config = config
        self._backend = _BlobStorageBackend(config)

    async def initialize(self) -> None:
        await self._backend.initialize()

    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs: Any
    ) -> StorageReadResult[StoreItemT]:
        read_options = {"timeout": 5, **kwargs}
        document = await self._backend.read(key, **read_options)
        if document is None:
            return cast(
                StorageReadResult[StoreItemT],
                StorageReadResult(key=key, status=StorageOperationStatus.NOT_FOUND),
            )
        value = cast(
            StoreItemT,
            target_cls.from_json_to_store_item(json.loads(document.content)),
        )
        return cast(
            StorageReadResult[StoreItemT],
            StorageReadResult(
                key=key,
                status=StorageOperationStatus.SUCCEEDED,
                value=value,
                version=document.version,
            ),
        )

    async def _write_item(
        self,
        key: str,
        value: StoreItem,
        options: StorageWriteOptions,
    ) -> StorageWriteResult:
        payload = json.dumps(value.store_item_to_json()).encode("utf-8")
        try:
            condition_version = (
                options.expected_version
                if options.expected_version is not None
                else "*" if options.mode == StorageWriteMode.REPLACE else None
            )
            version = await self._backend.write(
                key,
                payload,
                overwrite=options.mode != StorageWriteMode.CREATE_ONLY,
                etag=condition_version,
                match_condition=(
                    MatchConditions.IfNotModified
                    if condition_version is not None
                    else None
                ),
            )
            return StorageWriteResult(
                key=key,
                status=StorageOperationStatus.SUCCEEDED,
                version=version,
            )
        except Exception as error:  # noqa: BLE001
            status_code = _status_code(error)
            if (
                options.mode == StorageWriteMode.CREATE_ONLY
                and status_code in (409, 412)
                and options.expected_version is not None
            ):
                current_version = await self._backend.get_version(key)
                return StorageWriteResult(
                    key=key,
                    status=(
                        StorageOperationStatus.CONFLICT
                        if current_version is not None
                        else StorageOperationStatus.CONDITION_NOT_MET
                    ),
                    version=current_version,
                )
            if options.mode == StorageWriteMode.CREATE_ONLY and (
                status_code == 409
                or (status_code == 412 and options.expected_version is None)
            ):
                return StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.CONFLICT,
                    version=await self._backend.get_version(key),
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
                    status=(
                        StorageOperationStatus.NOT_FOUND
                        if options.mode == StorageWriteMode.REPLACE
                        and options.expected_version is None
                        else StorageOperationStatus.CONDITION_NOT_MET
                    ),
                    version=await self._backend.get_version(key),
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
            if _status_code(error) == 404:
                return StorageDeleteResult(
                    key=key,
                    status=(
                        StorageOperationStatus.CONDITION_NOT_MET
                        if options.expected_version is not None
                        else StorageOperationStatus.NOT_FOUND
                    ),
                )
            if _status_code(error) == 412:
                return StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.CONDITION_NOT_MET,
                    version=await self._backend.get_version(key),
                )
            raise

    async def close(self) -> None:
        """Close the Azure clients owned by this adapter."""
        await self._backend.close()

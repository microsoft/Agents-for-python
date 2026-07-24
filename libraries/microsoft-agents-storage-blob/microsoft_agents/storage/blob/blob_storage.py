import json
from typing import TypeVar
from io import BytesIO

from azure.storage.blob.aio import (
    ContainerClient,
    BlobServiceClient,
)

from microsoft_agents.hosting.core.storage import StoreItem
from microsoft_agents.hosting.core.storage.storage import AsyncStorageBase
from microsoft_agents.hosting.core.storage._type_aliases import JSON
from microsoft_agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)
from microsoft_agents.storage.blob.errors import blob_storage_errors

from .blob_storage_config import BlobStorageConfig

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class BlobStorage(AsyncStorageBase):
    """A Blob Storage provider for storing StoreItem objects in Azure Blob Storage."""

    def __init__(self, config: BlobStorageConfig):
        """Initialize the BlobStorage with the given configuration.

        :param config: BlobStorageConfig object containing the configuration for the blob storage.
        :raises ValueError: If the container name is not provided in the configuration.
        """

        if not config.container_name:
            raise ValueError(str(blob_storage_errors.BlobContainerNameRequired))

        self.config = config

        self._blob_service_client: BlobServiceClient = self._create_client()
        self._container_client: ContainerClient = (
            self._blob_service_client.get_container_client(config.container_name)
        )
        self._initialized: bool = False

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
        self, key: str, *, target_cls: StoreItemT, **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Reads an item from blob storage.

        :param key: The key of the item to read.
        :param target_cls: The class type of the StoreItem to deserialize into.
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
            return key, target_cls.from_json_to_store_item(item_JSON)
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

    async def _close(self) -> None:
        """Cleans up the storage resources."""
        await self._container_client.close()
        await self._blob_service_client.close()

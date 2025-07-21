import json
from typing import TypeVar, Union
from io import BytesIO

from azure.storage.blob.aio import (
    ContainerClient,
    BlobServiceClient,
)

from microsoft.agents.hosting.core.storage import StoreItem
from microsoft.agents.hosting.core.storage.storage import AsyncStorageBase
from microsoft.agents.hosting.core.storage._type_aliases import JSON
from microsoft.agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)

from .blob_storage_config import BlobStorageConfig

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class BlobStorage(AsyncStorageBase):

    def __init__(self, config: BlobStorageConfig):

        if not config.container_name:
            raise ValueError("BlobStorage: Container name is required.")

        self.config = config

        blob_service_client: BlobServiceClient = self._create_client()
        self._container_client: ContainerClient = (
            blob_service_client.get_container_client(config.container_name)
        )
        self._initialized: bool = False

    def _create_client(self) -> BlobServiceClient:
        if self.config.url:  # connect with URL and credentials
            if not self.config.credential:
                raise ValueError(
                    "BlobStorage: Credential is required when using a custom service URL."
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
        self, key: str, *, target_cls: StoreItemT = None, **kwargs
    ) -> tuple[Union[str, None], Union[StoreItemT, None]]:
        item = await ignore_error(
            self._container_client.download_blob(blob=key),
            is_status_code_error(404),
        )
        if not item:
            return None, None

        item_rep: str = await item.readall()
        item_JSON: JSON = json.loads(item_rep)
        try:
            return key, target_cls.from_json_to_store_item(item_JSON)
        except AttributeError as error:
            raise TypeError(
                f"BlobStorage.read_item(): could not deserialize blob item into {target_cls} class. Error: {error}"
            )

    async def _write_item(self, key: str, item: StoreItem) -> None:
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
        await ignore_error(
            self._container_client.delete_blob(blob=key), is_status_code_error(404)
        )

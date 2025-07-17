# based on
# https://github.com/microsoft/botbuilder-python/blob/main/libraries/botbuilder-azure/botbuilder/azure/blob_storage.py

from typing import TypeVar
from io import BytesIO
import json

from azure.core.exceptions import (
    HttpResponseError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from azure.storage.blob.aio import (
    ContainerClient,
    BlobServiceClient,
)

from microsoft.agents.storage._type_aliases import JSON
from microsoft.agents.storage import Storage, StoreItem

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class BlobStorageSettings:

    def __init__(
        self,
        container_name: str,
        account_name: str = "",
        account_key: str = "",
        connection_string: str = "",
    ):
        self.container_name = container_name
        self.account_name = account_name
        self.account_key = account_key
        self.connection_string = connection_string


def convert_account_name_and_key_to_connection_string(settings: BlobStorageSettings):
    if not settings.account_name or not settings.account_key:
        raise ValueError(
            "account_name and account_key are both required for BlobStorageSettings if not using a connections string."
        )
    return (
        f"DefaultEndpointsProtocol=https;AccountName={settings.account_name};"
        f"AccountKey={settings.account_key};EndpointSuffix=core.windows.net"
    )


class BlobStorage(Storage):

    def __init__(self, settings: BlobStorageSettings):
        if not settings.container_name:
            raise ValueError("BlobStorage: Container name is required.")

        connection_string: str = settings.connection_string
        if not connection_string:
            # New Azure Blob SDK only allows connection strings, but our SDK allows key+name.
            # This is here for backwards compatibility.
            connection_string = convert_account_name_and_key_to_connection_string(
                settings
            )

        blob_service_client: BlobServiceClient = (
            BlobServiceClient.from_connection_string(connection_string)
        )

        self._container_client: ContainerClient = (
            blob_service_client.get_container_client(settings.container_name)
        )
        self._initialized: bool = False

    async def _initialize_container(self):
        """Initializes the storage container"""
        if self._initialized is False:
            # This should only happen once - assuming this is a singleton.
            # ContainerClient.exists() method is available in an unreleased version of the SDK. Until then, we use:
            try:
                await self._container_client.create_container()
            except ResourceExistsError:
                pass
            self._initialized = True

        return self._initialized

    async def read(
        self, keys: list[str], *, target_cls: StoreItemT = None, **kwargs
    ) -> dict[str, StoreItemT]:
        """Retrieve entities from the configured blob container.

        :param keys: An array of entity keys.
        :type keys: dict[str, StoreItem]
        :param target_cls: The StoreItem class to deserialize retrieved values into.
        :type target_cls: StoreItem
        :return dict:
        """
        if not keys:
            raise ValueError("BlobStorage.read(): Keys are required when reading.")
        if not target_cls:
            raise ValueError("BlobStorage.read(): target_cls cannot be None.")

        await self._initialize_container()

        result: dict[str, StoreItem] = {}
        for key in keys:

            try:
                item_rep: str = await (
                    await self._container_client.download_blob(blob=key)
                ).readall()
                item_JSON: JSON = json.loads(item_rep)
            except HttpResponseError as error:
                if error.status_code == 404:
                    continue
                else:
                    raise HttpResponseError(
                        f"BlobStorage.read(): Error reading blob '{key}': {error}"
                    )

            try:
                result[key] = target_cls.from_json_to_store_item(item_JSON)
            except AttributeError as error:
                raise TypeError(
                    f"BlobStorage.read(): could not deserialize blob item into {target_cls} class. Error: {error}"
                )

        return result

    async def write(self, changes: dict[str, StoreItem]):
        """Stores a new entity in the configured blob container.

        :param changes: The changes to write to storage.
        :type changes: dict[str, StoreItem]
        :return:
        """
        if not changes:
            raise ValueError("BlobStorage.write(): changes cannot be None nor empty")

        await self._initialize_container()

        for key, item in changes.items():

            item_JSON: JSON = item.store_item_to_json()
            if item_JSON is None:
                raise ValueError(
                    "BlobStorage.write(): StoreItem serialization cannot return None"
                )
            item_rep_bytes = json.dumps(item_JSON).encode("utf-8")

            # providing the length parameter may improve performance
            await self._container_client.upload_blob(
                name=key,
                data=BytesIO(item_rep_bytes),
                overwrite=True,
                length=len(item_rep_bytes),
            )

    async def delete(self, keys: list[str]):
        """Deletes entity blobs from the configured container.

        :param keys: An array of entity keys.
        :type keys: list[str]
        """
        if keys is None:
            raise ValueError("BlobStorage.delete(): keys parameter can't be null")

        await self._initialize_container()

        for key in keys:
            try:
                await self._container_client.delete_blob(blob=key)
            # We can't delete what's already gone.
            except ResourceNotFoundError:
                pass

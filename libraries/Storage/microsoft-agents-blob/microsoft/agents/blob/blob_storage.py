# based on
# https://github.com/microsoft/botbuilder-python/blob/main/libraries/botbuilder-azure/botbuilder/azure/blob_storage.py

from typing import TypeVar
import json

from microsoft.agents.storage._type_aliases import JSON

from azure.core import MatchConditions
from azure.core.exceptions import (
    HttpResponseError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from azure.storage.blob.aio import BlobServiceClient

from microsoft.agents.storage import Storage, StoreItem

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class BlobStorageSettings:

    def __init__(
        self,
        container_name: str,
        account_name: str = "",
        account_key: str = "",
        connection_string: str = ""
    ):

        self.container_name = container_name
        self.account_name = account_name
        self.account_key = account_key
        self.connection_string = connection_string

# New Azure Blob SDK only allows connection strings, but our SDK allows key+name.
# This is here for backwards compatibility.
def convert_account_name_and_key_to_connection_string(settings: BlobStorageSettings):
    if not settings.account_name or not settings.account_key:
        raise Exception(
            "account_name and account_key are both required for BlobStorageSettings if not using a connections string."
        )
    return (
        f"DefaultEndpointsProtocol=https;AccountName={settings.account_name};"
        f"AccountKey={settings.account_key};EndpointSuffix=core.windows.net"
    )

class BlobStorage(Storage):

    def __init__(self, settings: BlobStorageSettings):

        if not settings.container_name:
            raise Exception("Container name is required.")

        if settings.connection_string:
            blob_service_client = BlobServiceClient.from_connection_string(
                settings.connection_string
            )
        else:
            blob_service_client = BlobServiceClient.from_connection_string(
                convert_account_name_and_key_to_connection_string(settings)
            )

        self.__container_client = blob_service_client.get_container_client(
            settings.container_name
        )

        self.__initialized = False

    async def _initialize(self):

        if self.__initialized is False:
            # This should only happen once - assuming this is a singleton.
            # ContainerClient.exists() method is available in an unreleased version of the SDK. Until then, we use:
            try:
                await self.__container_client.create_container()
            except ResourceExistsError:
                pass
            self.__initialized = True
        return self.__initialized

    async def read(
            self,
            keys: list[str],
            *,
            target_cls: StoreItemT = None,
            **kwargs
        ) -> dict[str, StoreItemT]:
        """Retrieve entities from the configured blob container.

        :param keys: An array of entity keys.
        :type keys: dict[str, StoreItem]
        :return dict:
        """
        if not keys:
            raise Exception("Keys are required when reading")

        await self._initialize()

        result: dict[str, StoreItem] = {}

        for key in keys:

            blob_client = self.__container_client.get_blob_client(key)

            try:
                blob = await blob_client.download_blob()
            except HttpResponseError as error:
                if error.status_code == 404:
                    continue

            item_json = json.loads(await blob.content_as_text())
            
            item_json["e_tag"] = blob.properties.etag.replace('""', "")

            if not target_cls:
                result[key] = item_json
            else:
                try:
                    result[key] = target_cls.from_json_to_store_item(item_json)
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

        if changes is None:
            raise ValueError("BlobStorage.write(): changes cannot be None")
        
        for key, item in changes.items():

            item_json = item.store_item_to_json()
            if item_json is None:
                raise ValueError("BlobStorage.write(): StoreItem serialization cannot return None")

            item_str = json.dumps(item_json)
            
            blob_reference = self.__container_client.get_blob_client(key)

            e_tag = None if item_json is None else item_json.get("e_tag", None)
            e_tag = None if e_tag == "*" else e_tag

            if e_tag == "":
                raise Exception("blob_storage.write(): etag missing")

            if e_tag:
                await blob_reference.upload_blob(
                    item_str, match_condition=MatchConditions.IfNotModified, etag=e_tag
                )
            else:
                await blob_reference.upload_blob(item_str, overwrite=True)

    async def delete(self, keys: list[str]):
        """Deletes entity blobs from the configured container.

        :param keys: An array of entity keys.
        :type keys: list[str]
        """

        if keys is None:
            raise Exception("BlobStorage.delete: keys parameter can't be null")

        await self._initialize()

        for key in keys:
            blob_client = self.__container_client.get_blob_client(key)
            try:
                await blob_client.delete_blob()
            # We can't delete what's already gone.
            except ResourceNotFoundError:
                pass
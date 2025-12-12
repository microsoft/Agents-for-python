import json
import gc
import os
from io import BytesIO
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

from tests._common.storage.utils import (
    CRUDStorageTests,
    QuickCRUDStorageTests,
    StorageBaseline,
    MockStoreItem,
    MockStoreItemB,
)

async def reset_container(container_client):

    try:
        # blobs = []

        async for blob in container_client.list_blobs(timeout=5):
            await container_client.delete_blob(blob.name, timeout=5)
    except ResourceNotFoundError:
        pass
    # except Exception as e:
    #     breakpoint()

@asynccontextmanager
async def blob_storage_instance(existing=False):
    # Default Azure Storage Emulator connection string
    load_dotenv()
    connection_string = os.environ.get("TEST_BLOB_STORAGE_CONNECTION_STRING")
    if not connection_string:
        cred = DefaultAzureCredential()
        account_url = os.environ.get("TEST_BLOB_STORAGE_ACCOUNT_URL")

        blob_service_client = BlobServiceClient(account_url, credential=cred)
    else:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_name = "asdkunittest"

    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not existing:
            try:
                await reset_container(container_client)
            except Exception:
                pass
    except ResourceNotFoundError:
        container_client = await blob_service_client.create_container(container_name)

    if connection_string:
        blob_storage_config = BlobStorageConfig(
            container_name=container_name,
            connection_string=connection_string,
        )
    else:
        blob_storage_config = BlobStorageConfig(
            container_name=container_name,
            url=account_url,
            credential=cred,
        )

    storage = BlobStorage(blob_storage_config)

    yield storage, container_client

    await storage._container_client.close()
    await storage._blob_service_client.close()
    await container_client.close()
    await blob_service_client.close()

# @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
@pytest.mark.blob
class TestBlobStorage(QuickCRUDStorageTests):

    @asynccontextmanager
    async def storage(self, initial_data=None, existing=False):

        async with blob_storage_instance(existing=existing) as (storage, client):

            if not initial_data:
                initial_data = {}

            for key, value in initial_data.items():
                value_rep = json.dumps(value.store_item_to_json())
                await client.upload_blob(name=key, data=value_rep, overwrite=True)
                
            yield storage

    @pytest.mark.asyncio
    async def test_initialize(self):
        async with self.storage() as blob_storage:
            await blob_storage.initialize()
            await blob_storage.initialize()
            await blob_storage.write(
                {"key": MockStoreItem({"id": "item", "value": "data"})}
            )
            await blob_storage.initialize()
            assert (await blob_storage.read(["key"], target_cls=MockStoreItem)) == {
                "key": MockStoreItem({"id": "item", "value": "data"})
            }

    @pytest.mark.asyncio
    async def test_external_change_is_visible(self):
        async with blob_storage_instance() as (blob_storage, container_client):
            assert (await blob_storage.read(["key"], target_cls=MockStoreItem)) == {}
            assert (await blob_storage.read(["key2"], target_cls=MockStoreItem)) == {}
            await container_client.upload_blob(
                name="key", data=json.dumps({"id": "item", "value": "data"}), overwrite=True
            )
            await container_client.upload_blob(
                name="key2",
                data=json.dumps({"id": "another_item", "value": "new_val"}),
                overwrite=True,
            )
            assert (await blob_storage.read(["key"], target_cls=MockStoreItem))[
                "key"
            ] == MockStoreItem({"id": "item", "value": "data"})
            assert (await blob_storage.read(["key2"], target_cls=MockStoreItem))[
                "key2"
            ] == MockStoreItem({"id": "another_item", "value": "new_val"})

    @pytest.mark.asyncio
    async def test_blob_storage_flow_existing_container_and_persistence(self):

        async with blob_storage_instance(existing=True) as (storage, container_client):
            initial_data = {
                "item1": MockStoreItem({"id": "item1", "value": "data1"}),
                "__some_key": MockStoreItem({"id": "item2", "value": "data2"}),
                "!another_key": MockStoreItem({"id": "item3", "value": "data3"}),
                "1230": MockStoreItemB({"id": "item8", "value": "data"}, False),
                "key-with-dash": MockStoreItem({"id": "item4", "value": "data"}),
                "key.with.dot": MockStoreItem({"id": "item5", "value": "data"}),
                "key/with/slash": MockStoreItem({"id": "item6", "value": "data"}),
                "another key": MockStoreItemB({"id": "item7", "value": "data"}, True),
            }

            baseline_storage = StorageBaseline(initial_data)

            for key, value in initial_data.items():
                value_rep = json.dumps(value.store_item_to_json()).encode("utf-8")
                await container_client.upload_blob(
                    name=key, data=BytesIO(value_rep), overwrite=True
                )

            assert await baseline_storage.equals(storage)
            assert (
                await storage.read(["1230", "!another key"], target_cls=MockStoreItemB)
            ) == baseline_storage.read(["1230", "!another key"])

            changes = {
                "item1": MockStoreItem({"id": "item1", "value": "data1_changed"}),
                "__some_key": MockStoreItem({"id": "item2", "value": "data2_changed"}),
                "new_item": MockStoreItem({"id": "new_item", "value": "new_data"}),
            }

            baseline_storage.write(changes)
            await storage.write(changes)


            baseline_storage.delete(["another_key!", "item1"])
            await storage.delete(["another_key!", "item1"])
            assert await baseline_storage.equals(storage)

            blob_client = container_client.get_blob_client("item1")
            with pytest.raises(ResourceNotFoundError):
                await (await blob_client.download_blob()).readall()
            await blob_client._client.close()

            blob_client = container_client.get_blob_client("1230")
            item = await (await blob_client.download_blob()).readall()
            assert (
                MockStoreItemB.from_json_to_store_item(json.loads(item))
                == initial_data["1230"]
            )
            await blob_client._client.close()

            await reset_container(container_client)
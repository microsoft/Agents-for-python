import json
import gc
import os
from io import BytesIO

import pytest
import pytest_asyncio

from microsoft.agents.storage.blob import BlobStorage, BlobStorageConfig
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

from microsoft.agents.hosting.core.storage.storage_test_utils import (
    CRUDStorageTests,
    StorageBaseline,
    MockStoreItem,
    MockStoreItemB,
)

EMULATOR_RUNNING = False


async def blob_storage_instance(existing=False):

    # Default Azure Storage Emulator connection string
    connection_string = (
        "AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq"
        + "2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint="
        + "http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
        + "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
    )

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_name = "asdkunittest"

    if not existing:

        # reset state of test container
        try:
            container_client = blob_service_client.get_container_client(container_name)
            await container_client.delete_container()
        except ResourceNotFoundError:
            pass

        container_client = await blob_service_client.create_container(container_name)
    else:
        container_client = blob_service_client.get_container_client(container_name)

    blob_storage_config = BlobStorageConfig(
        container_name=container_name,
        connection_string=connection_string,
    )

    storage = BlobStorage(blob_storage_config)
    return storage, container_client


@pytest_asyncio.fixture
async def blob_storage():

    # setup
    storage, container_client = await blob_storage_instance()

    yield storage

    # teardown
    await container_client.delete_container()


@pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
class TestBlobStorage(CRUDStorageTests):

    async def storage(self, initial_data=None, existing=False):
        if not initial_data:
            initial_data = {}
        storage, container_client = await blob_storage_instance(existing=existing)

        for key, value in initial_data.items():
            value_rep = json.dumps(value.store_item_to_json())
            await container_client.upload_blob(name=key, data=value_rep, overwrite=True)

        return storage

    @pytest.mark.asyncio
    async def test_initialize(self, blob_storage):
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
        blob_storage, container_client = await blob_storage_instance()
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

        connection_string = (
            "AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq"
            + "2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint="
            + "http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
            + "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
        )
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_name = "asdkunittestpopulated"
        container_client = blob_service_client.get_container_client(container_name)

        # reset state of test container
        try:
            await container_client.delete_container()
        except ResourceNotFoundError:
            pass
        await container_client.create_container()

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

        blob_storage_config = BlobStorageConfig(
            container_name=container_name, connection_string=connection_string
        )

        storage = BlobStorage(blob_storage_config)

        assert await baseline_storage.equals(storage)
        assert (
            await storage.read(["1230", "another key"], target_cls=MockStoreItemB)
        ) == baseline_storage.read(["1230", "another key"])

        changes = {
            "item1": MockStoreItem({"id": "item1", "value": "data1_changed"}),
            "__some_key": MockStoreItem({"id": "item2", "value": "data2_changed"}),
            "new_item": MockStoreItem({"id": "new_item", "value": "new_data"}),
        }

        baseline_storage.write(changes)
        await storage.write(changes)

        baseline_storage.delete(["!another_key", "item1"])
        await storage.delete(["!another_key", "item1"])
        assert await baseline_storage.equals(storage)

        del storage
        gc.collect()

        blob_client = container_client.get_blob_client("item1")
        with pytest.raises(ResourceNotFoundError):
            await (await blob_client.download_blob()).readall()

        blob_client = container_client.get_blob_client("1230")
        item = await (await blob_client.download_blob()).readall()
        assert (
            MockStoreItemB.from_json_to_store_item(json.loads(item))
            == initial_data["1230"]
        )

        await container_client.delete_container()

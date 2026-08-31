import asyncio
import json
import gc
import os
from io import BytesIO
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig
from microsoft_agents.hosting.core.storage import (
    StorageDeleteOptions,
    StorageOperationStatus,
    StorageVersion,
    StorageWriteOptions,
)
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

from tests._common.storage.utils import (
    CRUDStorageTests,
    QuickCRUDStorageTests,
    StorageBaseline,
    MockStoreItem,
    MockStoreItemB,
)

# to enable blob tests, run with --run-blob
# also, make sure that .env has:
# TEST_BLOB_STORAGE_ACCOUNT_URL set


def test_blob_storage_config_defaults_to_v1_and_can_select_v2():
    assert BlobStorageConfig(container_name="test").storage_version == StorageVersion.V1
    assert (
        BlobStorageConfig(
            container_name="test", storage_version=StorageVersion.V2
        ).storage_version
        == StorageVersion.V2
    )


@pytest.mark.asyncio
async def test_v1_rejects_v2_options_instead_of_ignoring_them():
    storage = object.__new__(BlobStorage)
    storage.storage_version = StorageVersion.V1

    with pytest.raises(ValueError, match="write options require Storage V2"):
        await storage.write({"key": MockStoreItem()}, StorageWriteOptions())
    with pytest.raises(ValueError, match="delete options require Storage V2"):
        await storage.delete(["key"], StorageDeleteOptions())


class _ConcurrentCallBarrier:
    def __init__(self, expected: int):
        self._expected = expected
        self._active = 0
        self.max_active = 0
        self._ready = asyncio.Event()

    async def wait(self):
        self._active += 1
        self.max_active = max(self.max_active, self._active)
        if self._active == self._expected:
            self._ready.set()
        await asyncio.wait_for(self._ready.wait(), timeout=1)
        self._active -= 1


class _BlobDownloader:
    properties = {"etag": "v1"}

    def __init__(self, key: str):
        self._key = key

    async def readall(self):
        return json.dumps({"value": self._key}).encode()


class _ConcurrentBlobClient:
    def __init__(self, key: str, barrier: _ConcurrentCallBarrier):
        self._key = key
        self._barrier = barrier

    async def download_blob(self, **_kwargs):
        await self._barrier.wait()
        return _BlobDownloader(self._key)

    async def get_blob_properties(self):
        await self._barrier.wait()
        return {"etag": "v1"}

    async def upload_blob(self, *_args, **_kwargs):
        return {"etag": "v2"}

    async def delete_blob(self, **_kwargs):
        return None


class _ConcurrentBlobContainer:
    def __init__(self, barrier: _ConcurrentCallBarrier):
        self._barrier = barrier

    def get_blob_client(self, key: str):
        return _ConcurrentBlobClient(key, self._barrier)


def _create_v2_blob_storage(barrier: _ConcurrentCallBarrier):
    storage = object.__new__(BlobStorage)
    storage.storage_version = StorageVersion.V2
    storage._initialized = True
    storage._container_client = _ConcurrentBlobContainer(barrier)
    return storage


@pytest.mark.asyncio
async def test_v2_batches_run_independent_blob_operations_concurrently():
    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_blob_storage(barrier)
    read = await storage.read(["one", "two"], target_cls=MockStoreItem)
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in read.values()
    )
    assert barrier.max_active == 2

    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_blob_storage(barrier)
    write = await storage.write({"one": MockStoreItem(), "two": MockStoreItem()})
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in write.values()
    )
    assert barrier.max_active == 2

    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_blob_storage(barrier)
    delete = await storage.delete(["one", "two"])
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in delete.values()
    )
    assert barrier.max_active == 2


async def reset_container(container_client: ContainerClient):

    blobs = container_client.list_blobs(timeout=5)
    to_delete = []
    async for blob in blobs:
        to_delete.append(blob.name)

    for blob_name in to_delete:
        await container_client.delete_blob(blob_name, timeout=5)


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
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

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
                blob_client = await client.upload_blob(
                    name=key, data=value_rep, overwrite=True
                )
                await blob_client.close()

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
            blob_client = await container_client.upload_blob(
                name="key",
                data=json.dumps({"id": "item", "value": "data"}),
                overwrite=True,
            )
            await blob_client.close()
            blob_client = await container_client.upload_blob(
                name="key2",
                data=json.dumps({"id": "another_item", "value": "new_val"}),
                overwrite=True,
            )
            await blob_client.close()
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

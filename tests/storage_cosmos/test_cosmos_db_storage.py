# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import os
import gc
from contextlib import asynccontextmanager

import pytest

from dotenv import load_dotenv

from azure.cosmos import documents
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core import MatchConditions
from azure.identity.aio import DefaultAzureCredential

from microsoft_agents.storage.cosmos import (
    CosmosDBStorage,
    CosmosDBStorageConfig,
    CosmosDBStorageV2,
)
from microsoft_agents.storage.cosmos.cosmos_db_storage import _CosmosStorageBackend
from microsoft_agents.storage.cosmos.key_ops import sanitize_key
from microsoft_agents.hosting.core.storage import (
    StorageDeleteOptions,
    StorageOperationStatus,
    StorageWriteOptions,
    StorageWriteMode,
)

from tests._common.storage.utils import (
    QuickCRUDStorageTests,
    MockStoreItem,
    MockStoreItemB,
    StorageBaseline,
)

# to enable Cosmos DB tests, run with --run-cosmos
# also, make sure that .env has the following set:
#
# TEST_COSMOS_DB_ENDPOINT
# TEST_COSMOS_DB_AUTH_KEY


def create_config(compat_mode):

    load_dotenv()
    cosmos_db_endpoint = os.environ.get("TEST_COSMOS_DB_ENDPOINT")
    auth_key = os.environ.get("TEST_COSMOS_DB_AUTH_KEY")
    return CosmosDBStorageConfig(
        cosmos_db_endpoint=cosmos_db_endpoint,
        auth_key=auth_key,
        database_id="test-db",
        container_id="bot-storage",
        compatibility_mode=compat_mode,
    )


@pytest.fixture
def config():
    return create_config(compat_mode=False)


def test_public_cosmos_adapters_have_separate_implementations():
    assert not issubclass(CosmosDBStorage, CosmosDBStorageV2)
    assert not issubclass(CosmosDBStorageV2, CosmosDBStorage)


@pytest.mark.asyncio
async def test_v1_rejects_v2_options_instead_of_ignoring_them():
    storage = object.__new__(CosmosDBStorage)
    with pytest.raises(TypeError, match="positional argument"):
        await storage.write({"key": MockStoreItem()}, StorageWriteOptions())
    with pytest.raises(TypeError, match="positional argument"):
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


class _ConcurrentCosmosContainer:
    def __init__(self, barrier: _ConcurrentCallBarrier):
        self._barrier = barrier

    async def read_item(self, key, _partition_key):
        await self._barrier.wait()
        return {"id": key, "document": {"value": key}, "_etag": "v1"}

    async def upsert_item(self, **_kwargs):
        await self._barrier.wait()
        return {"_etag": "v2"}

    async def delete_item(self, *_args, **_kwargs):
        await self._barrier.wait()
        return None


def _create_v2_cosmos_storage(barrier: _ConcurrentCallBarrier):
    storage = object.__new__(CosmosDBStorageV2)
    backend = object.__new__(_CosmosStorageBackend)
    backend._container = _ConcurrentCosmosContainer(barrier)
    backend._sanitize = lambda key: key
    backend._get_partition_key = lambda key: key
    storage._backend = backend
    return storage


@pytest.mark.asyncio
async def test_v2_batches_run_independent_cosmos_operations_concurrently():
    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_cosmos_storage(barrier)
    read = await storage.read(["one", "two"], target_cls=MockStoreItem)
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in read.values()
    )
    assert barrier.max_active == 2

    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_cosmos_storage(barrier)
    write = await storage.write({"one": MockStoreItem(), "two": MockStoreItem()})
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in write.values()
    )
    assert barrier.max_active == 2

    barrier = _ConcurrentCallBarrier(2)
    storage = _create_v2_cosmos_storage(barrier)
    delete = await storage.delete(["one", "two"])
    assert all(
        result.status == StorageOperationStatus.SUCCEEDED for result in delete.values()
    )
    assert barrier.max_active == 2


class _StatusError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code


class _RecordingCosmosContainer:
    def __init__(self):
        self.read_calls = []
        self.create_calls = []
        self.upsert_calls = []
        self.replace_calls = []
        self.delete_calls = []
        self.replace_error = None
        self.delete_error = None

    async def read_item(self, *args, **kwargs):
        self.read_calls.append((args, kwargs))
        return {"_etag": "current", "document": {"value": "key"}}

    async def create_item(self, **kwargs):
        self.create_calls.append(kwargs)
        return {"_etag": "created"}

    async def upsert_item(self, **kwargs):
        self.upsert_calls.append(kwargs)
        return {"_etag": "upserted"}

    async def replace_item(self, **kwargs):
        self.replace_calls.append(kwargs)
        if self.replace_error:
            raise self.replace_error
        return {"_etag": "replaced"}

    async def delete_item(self, *args, **kwargs):
        self.delete_calls.append((args, kwargs))
        if self.delete_error:
            raise self.delete_error


class _CurrentCosmosReplaceContainer:
    """Model the current azure-cosmos replace_item call signature."""

    def __init__(self):
        self.replace_calls = []

    async def replace_item(self, *, item, body, etag=None, match_condition=None):
        self.replace_calls.append(
            {
                "item": item,
                "body": body,
                "etag": etag,
                "match_condition": match_condition,
            }
        )
        return {"_etag": "replaced"}


def _recording_v2_cosmos_storage(container):
    storage = object.__new__(CosmosDBStorageV2)
    backend = object.__new__(_CosmosStorageBackend)
    backend._container = container
    backend._sanitize = lambda key: key
    backend._get_partition_key = lambda key: f"partition:{key}"
    storage._backend = backend
    return storage


def _recording_v1_cosmos_storage(container):
    storage = object.__new__(CosmosDBStorage)
    backend = object.__new__(_CosmosStorageBackend)
    backend._container = container
    backend._sanitize = lambda key: key
    backend._get_partition_key = lambda key: f"partition:{key}"
    storage._backend = backend
    return storage


@pytest.mark.asyncio
async def test_v1_cosmos_write_still_rejects_an_empty_key():
    storage = _recording_v1_cosmos_storage(_RecordingCosmosContainer())

    with pytest.raises(ValueError, match="Key cannot be empty"):
        await storage.write({"": MockStoreItem()})


@pytest.mark.asyncio
async def test_v2_cosmos_write_uses_atomic_operation_for_each_mode():
    container = _RecordingCosmosContainer()
    storage = _recording_v2_cosmos_storage(container)

    await storage.write({"key": MockStoreItem()})
    await storage.write(
        {"key": MockStoreItem()},
        StorageWriteOptions(mode=StorageWriteMode.REPLACE),
    )
    await storage.write(
        {"key": MockStoreItem()}, StorageWriteOptions(expected_version="expected")
    )

    assert container.read_calls == []
    assert len(container.upsert_calls) == 1
    assert "partition_key" not in container.replace_calls[0]
    assert "etag" not in container.replace_calls[0]
    assert container.replace_calls[1]["etag"] == "expected"


@pytest.mark.asyncio
async def test_v2_cosmos_conditional_write_uses_current_replace_signature():
    container = _CurrentCosmosReplaceContainer()
    storage = _recording_v2_cosmos_storage(container)

    result = await storage.write(
        {"key": MockStoreItem()}, StorageWriteOptions(expected_version="expected")
    )

    assert result["key"].status == StorageOperationStatus.SUCCEEDED
    assert container.replace_calls == [
        {
            "item": "key",
            "body": {"id": "key", "realId": "key", "document": {}},
            "etag": "expected",
            "match_condition": MatchConditions.IfNotModified,
        }
    ]


@pytest.mark.asyncio
async def test_v2_cosmos_read_forwards_provider_options():
    container = _RecordingCosmosContainer()
    storage = _recording_v2_cosmos_storage(container)

    await storage.read(["key"], target_cls=MockStoreItem, consistency_level="Session")

    assert container.read_calls == [
        (("key", "partition:key"), {"consistency_level": "Session"})
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("storage_cls", [CosmosDBStorage, CosmosDBStorageV2])
async def test_cosmos_adapters_expose_public_close(storage_cls):
    class _ClosableClient:
        closed = False

        async def close(self):
            self.closed = True

    storage = object.__new__(storage_cls)
    backend = object.__new__(_CosmosStorageBackend)
    backend._client = _ClosableClient()
    storage._backend = backend

    await storage.close()

    assert storage._backend._client.closed


@pytest.mark.asyncio
async def test_v2_cosmos_conditional_missing_does_not_recreate_item():
    container = _RecordingCosmosContainer()
    container.replace_error = _StatusError(404)
    storage = _recording_v2_cosmos_storage(container)

    result = await storage.write(
        {"key": MockStoreItem()}, StorageWriteOptions(expected_version="expected")
    )

    assert result["key"].status == StorageOperationStatus.CONDITION_NOT_MET
    assert container.upsert_calls == []


@pytest.mark.asyncio
async def test_v2_cosmos_create_only_honors_expected_version_without_writing():
    container = _RecordingCosmosContainer()
    storage = _recording_v2_cosmos_storage(container)

    matching = await storage.write(
        {"key": MockStoreItem()},
        StorageWriteOptions(
            mode=StorageWriteMode.CREATE_ONLY, expected_version="current"
        ),
    )
    stale = await storage.write(
        {"key": MockStoreItem()},
        StorageWriteOptions(
            mode=StorageWriteMode.CREATE_ONLY, expected_version="stale"
        ),
    )

    assert matching["key"].status == StorageOperationStatus.CONFLICT
    assert stale["key"].status == StorageOperationStatus.CONFLICT
    assert container.create_calls == []


@pytest.mark.asyncio
async def test_v2_cosmos_delete_only_uses_condition_when_requested():
    container = _RecordingCosmosContainer()
    storage = _recording_v2_cosmos_storage(container)

    deleted = await storage.delete(["key"])
    container.delete_error = _StatusError(404)
    conditional = await storage.delete(
        ["key"], StorageDeleteOptions(expected_version="expected")
    )

    assert deleted["key"].status == StorageOperationStatus.SUCCEEDED
    assert container.delete_calls[0][1] == {}
    assert container.delete_calls[1][1]["etag"] == "expected"
    assert conditional["key"].status == StorageOperationStatus.CONDITION_NOT_MET
    assert container.read_calls == []


async def reset_container(container_client):

    try:
        items = []
        async for item in container_client.read_all_items():
            items.append(item)
        for item in items:
            await container_client.delete_item(item, partition_key=item.get("id"))
    except CosmosResourceNotFoundError:
        pass


@asynccontextmanager
async def create_cosmos_env(config, compat_mode=False, existing=False):
    """Creates the Cosmos DB environment for testing.

    If existing is False, creates a new database and container, deleting any
    existing ones with the same name. If existing is True, creates the database
    and container if they do not already exist."""

    cosmos_client = CosmosClient(
        config.cosmos_db_endpoint,
        config.auth_key,
    )

    if not existing:
        try:
            await cosmos_client.delete_database(config.database_id)
        except Exception:
            pass
        database = await cosmos_client.create_database(id=config.database_id)

        try:
            await reset_container(database.get_container_client(config.container_id))
        except Exception:
            pass

        partition_key = {
            "paths": ["/_partitionKey"] if compat_mode else ["/id"],
            "kind": documents.PartitionKind.Hash,
        }
        container_client = await database.create_container(
            id=config.container_id,
            partition_key=partition_key,
            offer_throughput=config.container_throughput,
        )
    else:
        database = await cosmos_client.create_database_if_not_exists(
            id=config.database_id
        )
        container_client = database.get_container_client(config.container_id)

    yield container_client

    await cosmos_client.close()


@asynccontextmanager
async def cosmos_db_storage_instance(compat_mode=False, existing=False):
    config = create_config(compat_mode)
    async with create_cosmos_env(
        config, compat_mode=compat_mode, existing=existing
    ) as container_client:
        storage = CosmosDBStorage(config)
        yield storage, container_client
        await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("test_require_compat", [True, False])
# @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
@pytest.mark.cosmos
async def test_cosmos_db_storage_flow_existing_container_and_persistence(
    test_require_compat,
):

    config = create_config(compat_mode=test_require_compat)
    async with create_cosmos_env(config) as container_client:

        initial_data = {
            "__some_key": MockStoreItem({"id": "item2", "value": "data2"}),
            "?test": MockStoreItem({"id": "?test", "value": "data1"}),
            "!another_key": MockStoreItem({"id": "item3", "value": "data3"}),
            "1230": MockStoreItemB({"id": "item8", "value": "data"}, False),
            "key-with-dash": MockStoreItem({"id": "item4", "value": "data"}),
            "key.with.dot": MockStoreItem({"id": "item5", "value": "data"}),
            "key/with/slash": MockStoreItem({"id": "item6", "value": "data"}),
            "another key": MockStoreItemB({"id": "item7", "value": "data"}, True),
        }

        baseline_storage = StorageBaseline(initial_data)

        for key, value in initial_data.items():
            doc = {
                "id": sanitize_key(
                    key,
                    config.key_suffix,
                    test_require_compat,
                ),
                "realId": key,
                "document": value.store_item_to_json(),
            }
            await container_client.upsert_item(body=doc)

        storage = CosmosDBStorage(config)
        assert await baseline_storage.equals(storage)
        assert (
            await storage.read(["1230", "another key"], target_cls=MockStoreItemB)
        ) == baseline_storage.read(["1230", "another key"])

        changes = {
            "?test": MockStoreItem({"id": "?test", "value": "data1_changed"}),
            "__some_key": MockStoreItem({"id": "item2", "value": "data2_changed"}),
            "new_item": MockStoreItem({"id": "new_item", "value": "new_data"}),
        }

        baseline_storage.write(changes)
        await storage.write(changes)

        baseline_storage.delete(["!another_key", "?test"])
        await storage.delete(["!another_key", "?test"])
        assert await baseline_storage.equals(storage)

        del storage
        gc.collect()
        storage = CosmosDBStorage(config)

        escaped_key = storage._backend._sanitize("?test")
        with pytest.raises(CosmosResourceNotFoundError):
            await container_client.read_item(
                escaped_key, storage._backend._get_partition_key(escaped_key)
            )

        escaped_key = storage._backend._sanitize("1230")
        item = (
            await container_client.read_item(
                escaped_key, storage._backend._get_partition_key(escaped_key)
            )
        ).get("document")
        assert MockStoreItemB.from_json_to_store_item(item) == initial_data["1230"]


@pytest.mark.cosmos
class TestCosmosDBStorage(QuickCRUDStorageTests):

    def get_compat_mode(self):
        return False

    @asynccontextmanager
    async def storage(self, initial_data=None, existing=False):
        async with cosmos_db_storage_instance(
            compat_mode=self.get_compat_mode(), existing=existing
        ) as (storage, container_client):
            if initial_data:
                await storage.write(initial_data)
            yield storage

    @pytest.mark.asyncio
    async def test_initialize(self):
        async with self.storage() as cosmos_db_storage:
            await cosmos_db_storage.initialize()
            await cosmos_db_storage.initialize()
            await cosmos_db_storage.write(
                {"some_Key": MockStoreItem({"id": "123", "data": "value"})}
            )
            await cosmos_db_storage.initialize()
            assert (
                await cosmos_db_storage.read(["some_Key"], target_cls=MockStoreItem)
            ) == {"some_Key": MockStoreItem({"id": "123", "data": "value"})}

    @pytest.mark.asyncio
    async def test_external_change_is_visible(self):
        async with cosmos_db_storage_instance() as (cosmos_storage, container_client):
            assert (await cosmos_storage.read(["key"], target_cls=MockStoreItem)) == {}
            assert (await cosmos_storage.read(["key2"], target_cls=MockStoreItem)) == {}
            await container_client.upsert_item(
                {
                    "id": "key",
                    "realId": "key",
                    "document": {"id": "key", "value": "data"},
                    "partitionKey": "",
                }
            )
            await container_client.upsert_item(
                {
                    "id": "key2",
                    "realId": "key2",
                    "document": {"id": "key2", "value": "new_val"},
                    "partitionKey": "",
                }
            )
            assert (await cosmos_storage.read(["key"], target_cls=MockStoreItem))[
                "key"
            ] == MockStoreItem({"id": "key", "value": "data"})
            assert (await cosmos_storage.read(["key2"], target_cls=MockStoreItem))[
                "key2"
            ] == MockStoreItem({"id": "key2", "value": "new_val"})

    @pytest.mark.asyncio
    async def test_cosmos_db_from_azure_cred(self):
        load_dotenv()

        cred = DefaultAzureCredential()
        url = os.environ.get("TEST_COSMOS_DB_ENDPOINT")
        config = CosmosDBStorageConfig(
            url=url,
            credential=cred,
            database_id="test-db",
            container_id="bot-storage",
            compatibility_mode=False,
        )

        storage = CosmosDBStorage(config)

        await storage.write({"some_Key": MockStoreItem({"id": "123", "data": "value"})})

        res = await storage.read(["some_Key"], target_cls=MockStoreItem)
        assert res == {"some_Key": MockStoreItem({"id": "123", "data": "value"})}


# @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
@pytest.mark.cosmos
class TestCosmosDBStorageWithCompat(TestCosmosDBStorage):
    def get_compat_mode(self):
        return True

    @pytest.mark.asyncio
    async def test_cosmos_db_from_azure_cred(self):
        pass


# @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
@pytest.mark.cosmos
class TestCosmosDBStorageInit:

    def test_raises_error_when_suffix_provided_but_compat(self, config):
        config.auth_key = None
        config.compatibility_mode = True
        config.key_suffix = "_test"
        with pytest.raises(ValueError):
            CosmosDBStorage(config)

    def test_raises_error_when_no_database_id_provided(self, config):
        config.database_id = None
        with pytest.raises(ValueError):
            CosmosDBStorage(config)

    def test_raises_error_when_no_container_id_provided(self, config):
        config.container_id = None
        with pytest.raises(ValueError):
            CosmosDBStorage(config)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("compat_mode", [True, False])
    async def test_raises_error_different_partition_key(self, compat_mode):
        config = create_config(compat_mode=compat_mode)
        async with create_cosmos_env(
            config, compat_mode=compat_mode
        ) as container_client:
            storage = CosmosDBStorage(config)

            with pytest.raises(Exception):

                cosmos_client = CosmosClient(
                    config.cosmos_db_endpoint,
                    config.auth_key,
                )
                try:
                    await cosmos_client.delete_database(config.database_id)
                except Exception:
                    pass
                database = await cosmos_client.create_database(id=config.database_id)

                try:
                    await database.delete_container(config.container_id)
                except Exception:
                    pass

                partition_key = {
                    "paths": ["/fake_part_key"],
                    "kind": documents.PartitionKind.Hash,
                }
                container_client = await database.create_container(
                    id=config.container_id,
                    partition_key=partition_key,
                    offer_throughput=config.container_throughput,
                )
                storage = CosmosDBStorage(config)
                await storage.initialize()
            await storage.close()
            await cosmos_client.close()

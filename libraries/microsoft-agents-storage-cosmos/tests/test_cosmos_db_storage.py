# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import gc

import pytest
import pytest_asyncio

from azure.cosmos import documents
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from microsoft.agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig
from microsoft.agents.storage.cosmos.key_ops import sanitize_key

from microsoft.agents.hosting.core.storage.storage_test_utils import (
    QuickCRUDStorageTests,
    MockStoreItem,
    MockStoreItemB,
    StorageBaseline,
)

EMULATOR_RUNNING = False


def create_config(compat_mode):
    return CosmosDBStorageConfig(
        cosmos_db_endpoint="https://localhost:8081",
        auth_key=(
            "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGG"
            "yPMbIZnqyMsEcaGQy67XIw/Jw=="
        ),
        database_id="test-db",
        container_id="bot-storage",
        compatibility_mode=compat_mode,
        container_throughput=800,
    )


@pytest.fixture
def config():
    return create_config(compat_mode=False)


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
            await database.delete_container(config.container_id)
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

    return container_client


async def cosmos_db_storage_instance(compat_mode=False, existing=False):
    config = create_config(compat_mode)
    container_client = await create_cosmos_env(
        config, compat_mode=compat_mode, existing=existing
    )
    storage = CosmosDBStorage(config)
    return storage, container_client


@pytest_asyncio.fixture()
async def cosmos_db_storage():
    storage, _ = await cosmos_db_storage_instance()
    return storage


@pytest.mark.asyncio
@pytest.mark.parametrize("test_require_compat", [True, False])
@pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
async def test_cosmos_db_storage_flow_existing_container_and_persistence(
    test_require_compat,
):

    config = create_config(compat_mode=test_require_compat)
    container_client = await create_cosmos_env(config)

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

    escaped_key = storage._sanitize("?test")
    with pytest.raises(CosmosResourceNotFoundError):
        await container_client.read_item(
            escaped_key, storage._get_partition_key(escaped_key)
        )

    escaped_key = storage._sanitize("1230")
    item = (
        await container_client.read_item(
            escaped_key, storage._get_partition_key(escaped_key)
        )
    ).get("document")
    assert MockStoreItemB.from_json_to_store_item(item) == initial_data["1230"]


@pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
class TestCosmosDBStorage(QuickCRUDStorageTests):

    def get_compat_mode(self):
        return False

    async def storage(self, initial_data=None, existing=False):
        storage, _ = await cosmos_db_storage_instance(
            compat_mode=self.get_compat_mode(), existing=existing
        )
        if initial_data:
            await storage.write(initial_data)
        return storage

    @pytest.mark.asyncio
    async def test_initialize(self, cosmos_db_storage):
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
        cosmos_storage, container_client = await cosmos_db_storage_instance()
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


@pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
class TestCosmosDBStorageWithCompat(TestCosmosDBStorage):
    def get_compat_mode(self):
        return True


@pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
class TestCosmosDBStorageInit:

    def test_raises_error_when_no_endpoint_provided(self, config):
        config.cosmos_db_endpoint = None
        with pytest.raises(ValueError):
            CosmosDBStorage(config)

    def test_raises_error_when_no_auth_key_provided(self, config):
        config.auth_key = None
        with pytest.raises(ValueError):
            CosmosDBStorage(config)

    def test_raises_error_when_suffix_provided_but_compat(self, config):
        config.auth_key = None
        config.compatibility_mode = True
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
        await create_cosmos_env(config, compat_mode=compat_mode)
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

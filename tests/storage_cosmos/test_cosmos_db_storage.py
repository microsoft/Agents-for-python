# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import gc
from contextlib import asynccontextmanager

import pytest

from dotenv import load_dotenv

from azure.cosmos import documents
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig
from microsoft_agents.storage.cosmos.key_ops import sanitize_key

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
        await storage._close()


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
            await storage._close()
            await cosmos_client.close()

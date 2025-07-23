import asyncio

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json, gc
from io import BytesIO

from azure.cosmos import documents
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from microsoft.agents.cosmos import CosmosDBStorage, CosmosDBStorageConfig
from microsoft.agents.cosmos.key_ops import sanitize_key

from microsoft.agents.storage.storage_test_utils import (
    QuickCRUDStorageTests,
    MockStoreItem,
    MockStoreItemB,
    StorageBaseline,
    debug_print,
)


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


def create_cosmos_env(config, compat_mode=False, existing=False):
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
            cosmos_client.delete_database(config.database_id)
        except Exception:
            pass
        database = cosmos_client.create_database(id=config.database_id)

        try:
            database.delete_container(config.container_id)
        except Exception:
            pass

        partition_key = {
            "paths": ["/_partitionKey"] if compat_mode else ["/id"],
            "kind": documents.PartitionKind.Hash,
        }
        container_client = database.create_container(
            id=config.container_id,
            partition_key=partition_key,
            offer_throughput=config.container_throughput,
        )
    else:
        database = cosmos_client.create_database_if_not_exists(id=config.database_id)
        container_client = database.get_container_client(config.container_id)

    return container_client


def cosmos_db_storage_instance(compat_mode=False, existing=False):
    config = create_config(compat_mode)
    container_client = create_cosmos_env(
        config, compat_mode=compat_mode, existing=existing
    )
    storage = CosmosDBStorage(config)
    return storage, container_client


async def main():

    # storage = CosmosDBStorage(config)
    # await storage.initialize()
    # await storage.write({"some-Key": MockStoreItem({"data": "value"})})
    # res = await storage.read(["some-Key"], target_cls=MockStoreItem)
    # print(res)

    initial_data = {
        "key1": MockStoreItem({"id": "key1", "value": 1}),
        "key3": MockStoreItem({"id": "key3", "value": 3}),
    }

    # client.

    storage, container = cosmos_db_storage_instance(compat_mode=True, existing=False)
    if initial_data:
        await storage.write(initial_data)

    from azure.cosmos.partition_key import NonePartitionKeyValue

    # print(container.read_item(
    #         "key1", partition_key=NonePartitionKeyValue))
    # print("\n"*5)

    # items = container.read_all_items(max_item_count=10)
    # for item in items:
    #     print(item)
    #     print("---")

    print(await storage.read(list(initial_data.keys()), target_cls=MockStoreItem))

    # print(items)

    return storage


if __name__ == "__main__":
    asyncio.run(main())

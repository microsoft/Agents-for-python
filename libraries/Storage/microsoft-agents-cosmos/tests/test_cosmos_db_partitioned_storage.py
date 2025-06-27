# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import pytest_asyncio

import azure.cosmos.exceptions as cosmos_exceptions
from azure.cosmos import documents

from microsoft.agents.storage import StoreItem
from microsoft.agents.storage._type_aliases import JSON
from microsoft.agents.cosmos import CosmosDbPartitionedStorage, CosmosDbPartitionedConfig


EMULATOR_RUNNING = False

@pytest.fixture()
def config():

    # setup
    database_id = "test-db"
    container_id = "bot-storage"

    config = CosmosDbPartitionedConfig(
        cosmos_db_endpoint="",
        auth_key="",
        database_id=database_id,
        container_id=container_id,
    )

    return config

@pytest_asyncio.fixture()
async def cosmos_storage(config):

    # setup
    storage: CosmosDbPartitionedStorage = CosmosDbPartitionedStorage(config)

    try:
        await storage.client.delete_database(config.database_id)
    except cosmos_exceptions.HttpResponseError:
        pass

    yield storage

    # teardown
    try:
        awai tstorage.client.delete_database(config.database_id)
    except cosmos_exceptions.HttpResponseError:
        pass

class TestCosmosDbPartitionedStorageConstructor:
    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_raises_error_when_instantiated_with_no_arguments(self):
        try:
            # noinspection PyArgumentList
            # pylint: disable=no-value-for-parameter
            CosmosDbPartitionedStorage()
        except Exception as error:
            assert error

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_raises_error_when_no_endpoint_provided(self, config):
        config.cosmos_db_endpoint = None
        try:
            CosmosDbPartitionedStorage(config)
        except Exception as error:
            assert error

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_raises_error_when_no_auth_key_provided(self, config):
        config.auth_key = None
        try:
            CosmosDbPartitionedStorage(config)
        except Exception as error:
            assert error

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_raises_error_when_no_database_id_provided(self, config):
        config.database_id = None
        try:
            CosmosDbPartitionedStorage(config)
        except Exception as error:
            assert error

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_raises_error_when_no_container_id_provided(self, config):
        config.container_id = None
        try:
            CosmosDbPartitionedStorage(config)
        except Exception as error:
            assert error

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_passes_cosmos_client_options(self, config):

        connection_policy = documents.ConnectionPolicy()
        connection_policy.DisableSSLVerification = True

        config.cosmos_client_options = {
            "connection_policy": connection_policy,
            "consistency_level": documents.ConsistencyLevel.Eventual,
        }

        client = CosmosDbPartitionedStorage(config)
        await client.initialize()

        assert (
            client.client.client_connection.connection_policy.DisableSSLVerification
            is True
        )
        assert (
            client.client.client_connection.default_headers["x-ms-consistency-level"]
            == documents.ConsistencyLevel.Eventual
        )


class TestCosmosDbPartitionedStorageBaseStorageTests:
    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_return_empty_object_when_reading_unknown_key(self, storage:
        test_ran = await StorageBaseTests.return_empty_object_when_reading_unknown_key(
            storage
        )
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_null_keys_when_reading(self, storage):
        test_ran = await StorageBaseTests.handle_null_keys_when_reading(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_null_keys_when_writing(self, storage):
        test_ran = await StorageBaseTests.handle_null_keys_when_writing(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_does_not_raise_when_writing_no_items(self, storage):
        test_ran = await StorageBaseTests.does_not_raise_when_writing_no_items(
            storage
        )
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_create_object(self, storage):
        test_ran = await StorageBaseTests.create_object(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_crazy_keys(self, storage):
        test_ran = await StorageBaseTests.handle_crazy_keys(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_update_object(self, storage):
        test_ran = await StorageBaseTests.update_object(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_delete_object(self, storage):
        test_ran = await StorageBaseTests.delete_object(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_perform_batch_operations(self, storage):
        test_ran = await StorageBaseTests.perform_batch_operations(storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_proceeds_through_waterfall(self, storage):
        test_ran = await StorageBaseTests.proceeds_through_waterfall(storage)
        assert test_ran
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# based on https://github.com/microsoft/botbuilder-python/blob/main/libraries/botbuilder-azure/tests/test_blob_storage.py

import pytest
import pytest_asyncio

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient

from microsoft.agents.storage import StoreItem
from microsoft.agents.storage._type_aliases import JSON
from microsoft.agents.blob import BlobStorage, BlobStorageSettings

from .storage_base_test import StorageBaseTests

EMULATOR_RUNNING = False

# constructs an emulated blob storage instance
@pytest_asyncio.fixture
async def blob_storage():
    
    # setup
    
    # Default Azure Storage Emulator connection string
    connection_string = ("AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq"
    + "2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint="
    + "http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    + "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_name = "test"
    container_client = blob_service_client.get_container_client(container_name)

    # reset state of test container
    try:
        await container_client.delete_container()
    except ResourceNotFoundError:
        pass
    await container_client.create_container()

    blob_storage_settings = BlobStorageSettings(
        account_name="", account_key="",
        container_name=container_name,
        connection_string=connection_string
    )

    storage = BlobStorage(blob_storage_settings)

    yield storage

    # teardown
    await container_client.delete_container()


class SimpleStoreItem(StoreItem):

    def __init__(self, counter: int = 1, value: str = "*"):
        self.counter = counter
        self.value = value

    def store_item_to_json(self) -> JSON:
        return {
            "counter": self.counter,
            "value": self.value,
        }

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "StoreItem":
        return SimpleStoreItem(json_data["counter"], json_data["value"])


class TestBlobStorageConstructor:

    @pytest.mark.asyncio
    async def test_blob_storage_init_should_error_without_container_name(self):
        settings = BlobStorageSettings("")
        with pytest.raises(Exception) as err:
            BlobStorage(settings)
            
        assert err.value.args[0] == "BlobStorage: Container name is required."

    @pytest.mark.asyncio
    async def test_blob_storage_init_should_error_without_blob_config(self):
        try:
            BlobStorage(BlobStorageSettings())  # pylint: disable=no-value-for-parameter
        except Exception as error:
            assert error

    @pytest.mark.asyncio
    async def test_blob_storage_init_should_error_with_insufficient_settings(self):
        settings_0 = BlobStorageSettings("norway", account_name="some_account_name")
        settings_1 = BlobStorageSettings("sweden", account_key="some_account_key")
        with pytest.raises(Exception) as err:
            BlobStorage(settings_0)
        with pytest.raises(Exception) as err:
            BlobStorage(settings_1)

    @pytest.mark.asyncio
    async def test_blob_storage_init_from_account_key_and_name(self):
        settings = BlobStorageSettings("norway", account_name="some_account_name", account_key="some_account_key")
        BlobStorage(settings)


class TestBlobStorageBaseTests:
    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_return_empty_object_when_reading_unknown_key(self, blob_storage):
        test_ran = await StorageBaseTests.return_empty_object_when_reading_unknown_key(
            blob_storage
        )
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_null_keys_when_reading(self, blob_storage):
        test_ran = await StorageBaseTests.handle_null_keys_when_reading(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_null_keys_when_writing(self, blob_storage):
        test_ran = await StorageBaseTests.handle_null_keys_when_writing(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def does_raise_when_writing_no_items(self, blob_storage):
        test_ran = await StorageBaseTests.does_raise_when_writing_no_items(
            blob_storage
        )
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_create_object(self, blob_storage):
        test_ran = await StorageBaseTests.create_object(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_handle_crazy_keys(self, blob_storage):
        test_ran = await StorageBaseTests.handle_crazy_keys(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_update_object(self, blob_storage):
        test_ran = await StorageBaseTests.update_object(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_delete_object(self, blob_storage):
        test_ran = await StorageBaseTests.delete_object(blob_storage)
        assert test_ran

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_perform_batch_operations(self, blob_storage):
        test_ran = await StorageBaseTests.perform_batch_operations(blob_storage)
        assert test_ran


class TestBlobStorage:

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_read_update_same_data(self, blob_storage):
        await blob_storage.write({"test": SimpleStoreItem(counter=1)})
        data_result = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        data_result["test"].counter = 2
        await blob_storage.write(data_result)
        data_updated = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        assert data_updated["test"].counter == 2
        assert data_updated["test"].value == data_result["test"].value

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_write_should_overwrite(
        self, blob_storage
    ):
        await blob_storage.write({"user": SimpleStoreItem()})
        await blob_storage.write({"user": SimpleStoreItem(counter=10, value="*")})
        data = await blob_storage.read(["user"], target_cls=SimpleStoreItem)
        assert data["user"].counter == 10
        assert data["user"].value == "*"

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_should_delete_according_cached_data(self, blob_storage):
        await blob_storage.write({"test": SimpleStoreItem()})
        try:
            await blob_storage.delete(["test"])
        except Exception as error:
            raise error
        else:
            data = await blob_storage.read(["test"], target_cls=SimpleStoreItem)

            assert isinstance(data, dict)
            assert not data.keys()

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_should_delete_multiple_values_when_given_multiple_valid_keys(
        self, blob_storage
    ):
        await blob_storage.write({"test": SimpleStoreItem(), "test2": SimpleStoreItem(2)})
        await blob_storage.delete(["test", "test2"])
        data = await blob_storage.read(["test", "test2"], target_cls=SimpleStoreItem)
        assert not data.keys()

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_should_delete_values_when_given_multiple_valid_keys_and_ignore_other_data(
        self, blob_storage
    ):
        await blob_storage.write(
            {
                "test": SimpleStoreItem(),
                "test2": SimpleStoreItem(counter=2),
                "test3": SimpleStoreItem(counter=3),
            }
        )
        await blob_storage.delete(["test", "test2"])
        data = await blob_storage.read(["test", "test2", "test3"], target_cls=SimpleStoreItem)
        assert len(data.keys()) == 1

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_invalid_key_should_do_nothing_and_not_affect_cached_data(
        self, blob_storage
    ):
        await blob_storage.write({"test": SimpleStoreItem()})
        await blob_storage.delete(["foo"])
        data = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        assert len(data.keys()) == 1
        data = await blob_storage.read(["foo"], target_cls=SimpleStoreItem)
        assert not data.keys()

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_invalid_keys_should_do_nothing_and_not_affect_cached_data(
        self, blob_storage
    ):
        await blob_storage.write({"test": SimpleStoreItem()})
        await blob_storage.delete(["foo", "bar"])
        data = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        assert len(data.keys()) == 1
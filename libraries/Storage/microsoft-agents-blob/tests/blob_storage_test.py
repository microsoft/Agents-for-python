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

EMULATOR_RUNNING = True

# constructs an emulated blob storage instance
@pytest_asyncio.fixture
async def blob_storage():
    
    # setup

    connection_string = ("AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq"
    + "2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint="
    + "http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    + "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_name = "test"
    container_client = blob_service_client.get_container_client(container_name)

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
    def __init__(self, counter=1, e_tag="*"):
        super(SimpleStoreItem, self).__init__()

        self.counter = counter
        self.e_tag = e_tag

    def store_item_to_json(self) -> JSON:
        return {
            "counter": self.counter,
            "e_tag": self.e_tag,
        }

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "StoreItem":
        return SimpleStoreItem(json_data["counter"], json_data["e_tag"])


class TestBlobStorageConstructor:

    @pytest.mark.asyncio
    async def test_blob_storage_init_should_error_without_blob_config(self):
        try:
            BlobStorage(BlobStorageSettings())  # pylint: disable=no-value-for-parameter
        except Exception as error:
            assert error


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
    async def test_does_not_raise_when_writing_no_items(self, blob_storage):

        test_ran = await StorageBaseTests.does_not_raise_when_writing_no_items(
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
    async def test_blob_storage_read_update_should_return_new_etag(self, blob_storage):
        await blob_storage.write({"test": SimpleStoreItem(counter=1)})
        data_result = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        data_result["test"].counter = 2
        await blob_storage.write(data_result)
        data_updated = await blob_storage.read(["test"], target_cls=SimpleStoreItem)
        assert data_updated["test"].counter == 2
        assert data_updated["test"].e_tag != data_result["test"].e_tag

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_write_should_overwrite_when_new_e_tag_is_an_asterisk(
        self, blob_storage
    ):
        await blob_storage.write({"user": SimpleStoreItem()})

        await blob_storage.write({"user": SimpleStoreItem(counter=10, e_tag="*")})
        data = await blob_storage.read(["user"], target_cls=SimpleStoreItem)
        assert data["user"].counter == 10

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
        data = await blob_storage.read(["test", "test2"])
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
        data = await blob_storage.read(["test", "test2", "test3"])
        assert len(data.keys()) == 1

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_invalid_key_should_do_nothing_and_not_affect_cached_data(
        self, blob_storage
    ):
        await blob_storage.write({"test": SimpleStoreItem()})

        await blob_storage.delete(["foo"])
        data = await blob_storage.read(["test"])
        assert len(data.keys()) == 1
        data = await blob_storage.read(["foo"])
        assert not data.keys()

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_invalid_keys_should_do_nothing_and_not_affect_cached_data(
        self, blob_storage
    ):
        await blob_storage.write({"test": SimpleStoreItem()})

        await blob_storage.delete(["foo", "bar"])
        data = await blob_storage.read(["test"])
        assert len(data.keys()) == 1
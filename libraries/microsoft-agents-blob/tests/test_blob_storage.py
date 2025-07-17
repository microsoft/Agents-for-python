# temporary fix for pytest import issue. There are two separate scripts here

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Adapted from https://github.com/microsoft/botbuilder-python/blob/main/libraries/botbuilder-testing/botbuilder/testing/storage_base_tests.py

Base tests that all storage providers should implement in their own tests.
They handle the storage-based assertions, internally.

All tests return true if assertions pass to indicate that the code ran to completion, passing internal assertions.
Therefore, all tests using theses static tests should strictly check that the method returns true.

:Example:
    async def test_handle_null_keys_when_reading(self):
        await reset()

        test_ran = await StorageBaseTests.handle_null_keys_when_reading(get_storage())

        assert test_ran
"""

import pytest

from microsoft.agents.storage import MemoryStorage, StoreItem
from microsoft.agents.storage._type_aliases import JSON


class MockStoreItem(StoreItem):

    def __init__(self, data: JSON = None):
        self.data = data or {}

    def store_item_to_json(self) -> JSON:
        return self.data

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "MockStoreItem":
        return MockStoreItem(json_data)


class StorageBaseTests:

    # pylint: disable=pointless-string-statement
    @staticmethod
    async def return_empty_object_when_reading_unknown_key(storage) -> bool:
        result = await storage.read(["unknown"], target_cls=MockStoreItem)

        assert result is not None
        assert len(result) == 0

        return True

    @staticmethod
    async def handle_null_keys_when_reading(storage) -> bool:
        if isinstance(storage, (MemoryStorage)):
            result = await storage.read(None, target_cls=MockStoreItem)
            assert len(result.keys()) == 0
        # Catch-all
        else:
            with pytest.raises(Exception) as err:
                await storage.read(None, target_cls=MockStoreItem)

        return True

    @staticmethod
    async def handle_null_keys_when_writing(storage) -> bool:
        with pytest.raises(Exception) as err:
            await storage.write(None)
        # assert err.value.args[0] == "Changes are required when writing"

        return True

    @staticmethod
    async def does_raise_when_writing_no_items(storage) -> bool:
        # noinspection PyBroadException
        with pytest.raises(Exception) as err:
            await storage.write(dict())
        return True

    @staticmethod
    async def create_object(storage) -> bool:
        store_items = {
            "createPoco": MockStoreItem({"id": 1}),
            "createPocoStoreItem": MockStoreItem({"id": 2, "value": "*"}),
        }

        await storage.write(store_items)

        read_store_items = await storage.read(
            store_items.keys(), target_cls=MockStoreItem
        )

        assert (
            store_items["createPoco"].data["id"]
            == read_store_items["createPoco"].data["id"]
        )
        assert (
            store_items["createPocoStoreItem"].data["id"]
            == read_store_items["createPocoStoreItem"].data["id"]
        )
        assert read_store_items["createPocoStoreItem"].data["value"] == "*"

        return True

    @staticmethod
    async def handle_crazy_keys(storage) -> bool:
        key = '!@#$%^&*()_+??><":QASD~`'
        store_item = MockStoreItem({"id": 1})
        store_items = {key: store_item}

        await storage.write(store_items)

        read_store_items = await storage.read(
            store_items.keys(), target_cls=MockStoreItem
        )

        assert read_store_items[key] is not None
        assert read_store_items[key].data["id"] == 1

        return True

    @staticmethod
    async def update_object(storage) -> bool:
        original_store_items = {
            "pocoItem": MockStoreItem({"id": 1, "count": 1}),
            "pocoStoreItem": MockStoreItem({"id": 1, "count": 1, "value": "*"}),
        }

        # 1st write should work
        await storage.write(original_store_items)

        loaded_store_items = await storage.read(
            ["pocoItem", "pocoStoreItem"], target_cls=MockStoreItem
        )

        update_poco_item = loaded_store_items["pocoItem"]
        update_poco_item.data["value"] = None
        update_poco_store_item = loaded_store_items["pocoStoreItem"]
        assert update_poco_store_item.data["value"] == "*"

        # 2nd write should work
        update_poco_item.data["count"] += 1
        update_poco_store_item.data["count"] += 1

        await storage.write(
            {
                key: MockStoreItem(value.data)
                for key, value in loaded_store_items.items()
            }
        )

        reloaded_store_items = await storage.read(
            loaded_store_items.keys(), target_cls=MockStoreItem
        )

        reloaded_update_poco_item = reloaded_store_items["pocoItem"]
        reloaded_update_poco_store_item = reloaded_store_items["pocoStoreItem"]

        assert reloaded_update_poco_item.data["count"] == 2
        assert reloaded_update_poco_store_item.data["count"] == 2
        assert reloaded_update_poco_item.data["value"] is None
        assert reloaded_update_poco_store_item.data["value"] == "*"

        return True

    @staticmethod
    async def delete_object(storage) -> bool:
        store_items = {"delete1": MockStoreItem({"id": 1, "count": 1, "value": "*"})}

        await storage.write(store_items)

        read_store_items = await storage.read(["delete1"], target_cls=MockStoreItem)

        assert read_store_items["delete1"].data["value"]
        assert read_store_items["delete1"].data["count"] == 1

        await storage.delete(["delete1"])

        reloaded_store_items = await storage.read(["delete1"], target_cls=MockStoreItem)

        assert reloaded_store_items.get("delete1", None) is None

        return True

    @staticmethod
    async def delete_unknown_object(storage) -> bool:
        # noinspection PyBroadException
        try:
            await storage.delete(["unknown_key"])
        except:
            pytest.fail("Should not raise")

        return True

    @staticmethod
    async def perform_batch_operations(storage) -> bool:
        await storage.write(
            {
                "batch1": MockStoreItem({"count": 10}),
                "batch2": MockStoreItem({"count": 20}),
                "batch3": MockStoreItem({"count": 30}),
            }
        )

        result = await storage.read(
            ["batch1", "batch2", "batch3"], target_cls=MockStoreItem
        )

        assert result.get("batch1", None) is not None
        assert result.get("batch2", None) is not None
        assert result.get("batch3", None) is not None
        assert result["batch1"].data["count"] == 10
        assert result["batch2"].data["count"] == 20
        assert result["batch3"].data["count"] == 30

        await storage.delete(["batch1", "batch2", "batch3"])

        result = await storage.read(
            ["batch1", "batch2", "batch3"], target_cls=MockStoreItem
        )

        assert result.get("batch1", None) is None
        assert result.get("batch2", None) is None
        assert result.get("batch3", None) is None

        return True


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


EMULATOR_RUNNING = False


# constructs an emulated blob storage instance
@pytest_asyncio.fixture
async def blob_storage():

    # setup

    # Default Azure Storage Emulator connection string
    connection_string = (
        "AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq"
        + "2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint="
        + "http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
        + "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
    )

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
        account_name="",
        account_key="",
        container_name=container_name,
        connection_string=connection_string,
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
        settings = BlobStorageSettings(
            "norway", account_name="some_account_name", account_key="some_account_key"
        )
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
        test_ran = await StorageBaseTests.does_raise_when_writing_no_items(blob_storage)
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
    async def test_blob_storage_write_should_overwrite(self, blob_storage):
        await blob_storage.write({"user": SimpleStoreItem()})
        await blob_storage.write({"user": SimpleStoreItem(counter=10, value="*")})
        data = await blob_storage.read(["user"], target_cls=SimpleStoreItem)
        assert data["user"].counter == 10
        assert data["user"].value == "*"

    @pytest.mark.skipif(not EMULATOR_RUNNING, reason="Needs the emulator to run.")
    @pytest.mark.asyncio
    async def test_blob_storage_delete_should_delete_according_cached_data(
        self, blob_storage
    ):
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
        await blob_storage.write(
            {"test": SimpleStoreItem(), "test2": SimpleStoreItem(2)}
        )
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
        data = await blob_storage.read(
            ["test", "test2", "test3"], target_cls=SimpleStoreItem
        )
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

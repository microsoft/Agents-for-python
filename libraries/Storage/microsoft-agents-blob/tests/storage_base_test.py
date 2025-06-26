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

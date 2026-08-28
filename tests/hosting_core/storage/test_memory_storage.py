from contextlib import asynccontextmanager

import pytest

from microsoft_agents.hosting.core.storage import (
    StorageDeleteOptions,
    StorageOperationStatus,
    StorageVersion,
    StorageWriteMode,
    StorageWriteOptions,
)
from microsoft_agents.hosting.core.storage.memory_storage import MemoryStorage
from tests._common.storage.utils import CRUDStorageTests
from tests._common.storage.utils import MockStoreItem


class _StoreItemShape:
    def __init__(self, data=None):
        self.data = data or {}

    def store_item_to_json(self):
        return self.data

    @classmethod
    def from_json_to_store_item(cls, data):
        return cls(data)


class TestMemoryStorage(CRUDStorageTests):

    @asynccontextmanager
    async def storage(self, initial_data=None):
        data = {
            key: value.store_item_to_json()
            for key, value in (initial_data or {}).items()
        }
        yield MemoryStorage(data)


@pytest.mark.asyncio
async def test_v2_returns_a_result_for_each_read_key():
    storage = MemoryStorage(storage_version=StorageVersion.V2)
    await storage.write({"existing": MockStoreItem({"value": 1})})

    results = await storage.read(["existing", "missing"], target_cls=MockStoreItem)

    assert results["existing"].status == StorageOperationStatus.SUCCEEDED
    assert results["existing"].value == MockStoreItem({"value": 1})
    assert results["existing"].version is not None
    assert results["missing"].status == StorageOperationStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_v2_create_replace_and_conditional_delete():
    storage = MemoryStorage(storage_version=StorageVersion.V2)
    created = await storage.write(
        {"key": MockStoreItem({"value": 1})},
        StorageWriteOptions(mode=StorageWriteMode.CREATE_ONLY),
    )
    duplicate = await storage.write(
        {"key": MockStoreItem({"value": 2})},
        StorageWriteOptions(mode=StorageWriteMode.CREATE_ONLY),
    )
    replaced = await storage.write(
        {"key": MockStoreItem({"value": 2})},
        StorageWriteOptions(
            mode=StorageWriteMode.REPLACE,
            expected_version=created["key"].version,
        ),
    )
    stale = await storage.write(
        {"key": MockStoreItem({"value": 3})},
        StorageWriteOptions(
            mode=StorageWriteMode.REPLACE,
            expected_version=created["key"].version,
        ),
    )
    deleted = await storage.delete(
        ["key"],
        StorageDeleteOptions(expected_version=replaced["key"].version),
    )

    assert created["key"].status == StorageOperationStatus.SUCCEEDED
    assert duplicate["key"].status == StorageOperationStatus.CONFLICT
    assert replaced["key"].status == StorageOperationStatus.SUCCEEDED
    assert stale["key"].status == StorageOperationStatus.CONDITION_NOT_MET
    assert deleted["key"].status == StorageOperationStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_v2_does_not_mutate_or_share_store_item_data():
    storage = MemoryStorage(storage_version=StorageVersion.V2)
    value = MockStoreItem({"nested": {"value": 1}})
    await storage.write({"key": value})
    value.data["nested"]["value"] = 2

    first = await storage.read(["key"], target_cls=MockStoreItem)
    first["key"].value.data["nested"]["value"] = 3
    second = await storage.read(["key"], target_cls=MockStoreItem)

    assert second["key"].value == MockStoreItem({"nested": {"value": 1}})


@pytest.mark.asyncio
async def test_v2_accepts_existing_store_item_shape_models():
    storage = MemoryStorage(storage_version=StorageVersion.V2)

    await storage.write({"key": _StoreItemShape({"value": 1})})
    result = await storage.read(["key"], target_cls=_StoreItemShape)

    assert result["key"].value.data == {"value": 1}


@pytest.mark.asyncio
async def test_v2_accepts_empty_batches_and_rejects_empty_version():
    storage = MemoryStorage(storage_version=StorageVersion.V2)

    assert await storage.read([], target_cls=MockStoreItem) == {}
    assert await storage.write({}) == {}
    assert await storage.delete([]) == {}
    with pytest.raises(ValueError, match="expected_version cannot be empty"):
        await storage.write(
            {"key": MockStoreItem()},
            StorageWriteOptions(expected_version=""),
        )

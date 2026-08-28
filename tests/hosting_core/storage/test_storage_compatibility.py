import pytest

from microsoft_agents.activity import AgentsModel
from microsoft_agents.hosting.core.storage import (
    Storage,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageOperationStatus,
    StorageReadResult,
    StorageWriteMode,
    StorageWriteOptions,
)
from microsoft_agents.hosting.core.storage.storage_compatibility import (
    as_storage,
    as_storage_v2,
    assert_storage_delete_succeeded,
    assert_storage_write_succeeded,
    get_storage_read_value,
)
from microsoft_agents.hosting.core.client.conversation_id_factory import (
    _implement_store_item_for_agents_model_cls,
)
from tests._common.storage.utils import MockStoreItem


class _LegacyStorage(Storage):
    def __init__(self):
        self.items = {}

    async def read(self, keys, *, target_cls, **kwargs):
        return {key: self.items[key] for key in keys if key in self.items}

    async def write(self, changes):
        self.items.update(changes)

    async def delete(self, keys):
        for key in keys:
            self.items.pop(key, None)


class _ModelItem(AgentsModel):
    value: str


@pytest.mark.asyncio
async def test_v1_adapter_returns_explicit_v2_results():
    storage = _LegacyStorage()
    await storage.write({"existing": MockStoreItem({"value": 1})})

    results = await as_storage_v2(storage).read(
        ["existing", "missing"], target_cls=MockStoreItem
    )

    assert results["existing"].status == StorageOperationStatus.SUCCEEDED
    assert results["missing"].status == StorageOperationStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_v1_adapter_rejects_unsupported_conditions():
    storage = as_storage_v2(_LegacyStorage())

    with pytest.raises(NotImplementedError, match='option "mode"'):
        await storage.write(
            {"key": MockStoreItem()},
            StorageWriteOptions(mode=StorageWriteMode.CREATE_ONLY),
        )
    with pytest.raises(NotImplementedError, match='option "expected_version"'):
        await storage.delete(["key"], StorageDeleteOptions(expected_version="1"))


@pytest.mark.asyncio
async def test_v2_adapter_exposes_legacy_storage_operations():
    legacy = _LegacyStorage()
    v2 = as_storage_v2(legacy)
    storage = as_storage(v2)

    await storage.write({"key": MockStoreItem({"value": 1})})

    assert await storage.read(["key"], target_cls=MockStoreItem) == {
        "key": MockStoreItem({"value": 1})
    }


def test_result_helpers_reject_missing_or_failed_results():
    assert (
        get_storage_read_value(
            {
                "key": StorageReadResult(
                    key="key", status=StorageOperationStatus.NOT_FOUND
                )
            },
            "key",
        )
        is None
    )
    with pytest.raises(RuntimeError, match='status "missing"'):
        assert_storage_write_succeeded({}, ["key"])
    with pytest.raises(RuntimeError, match='status "conditionNotMet"'):
        assert_storage_delete_succeeded(
            {
                "key": StorageDeleteResult(
                    key="key", status=StorageOperationStatus.CONDITION_NOT_MET
                )
            },
            ["key"],
        )


@pytest.mark.asyncio
async def test_v2_accepts_agents_model_store_item_shape():
    value = _ModelItem(value="one")
    _implement_store_item_for_agents_model_cls(value)
    storage = as_storage_v2(_LegacyStorage())

    await storage.write({"key": value})
    result = await storage.read(["key"], target_cls=_ModelItem)

    assert get_storage_read_value(result, "key") == value

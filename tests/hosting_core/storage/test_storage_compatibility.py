import pytest

from microsoft_agents.activity import AgentsModel
from microsoft_agents.hosting.core.storage import (
    Storage,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageOperationStatus,
    StorageReadResult,
    StorageReadResults,
    StorageWriteResults,
    StorageDeleteResults,
    StorageWriteMode,
    StorageWriteOptions,
)
from microsoft_agents.hosting.core.storage.storage_compatibility import (
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


def test_write_options_reject_invalid_mode():
    with pytest.raises(ValueError, match='mode "bogus"'):
        StorageWriteOptions(mode="bogus")  # type: ignore[arg-type]


def test_agents_model_store_item_serialization_uses_current_instance():
    first = _ModelItem(value="one")
    second = _ModelItem(value="two")
    _implement_store_item_for_agents_model_cls(first)

    assert first.store_item_to_json() == {"value": "one"}
    assert second.store_item_to_json() == {"value": "two"}


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


def test_result_helpers_reject_missing_or_failed_results():
    assert (
        get_storage_read_value(
            StorageReadResults(
                {
                    "key": StorageReadResult(
                        key="key", status=StorageOperationStatus.NOT_FOUND
                    )
                }
            ),
            "key",
        )
        is None
    )
    with pytest.raises(RuntimeError, match='status "missing"'):
        assert_storage_write_succeeded(StorageWriteResults(), ["key"])
    with pytest.raises(RuntimeError, match='status "conditionNotMet"'):
        assert_storage_delete_succeeded(
            StorageDeleteResults(
                {
                    "key": StorageDeleteResult(
                        key="key", status=StorageOperationStatus.CONDITION_NOT_MET
                    )
                }
            ),
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


def test_result_collections_expose_result_handling_behavior():
    reads = StorageReadResults(
        {
            "missing": StorageReadResult(
                key="missing", status=StorageOperationStatus.NOT_FOUND
            )
        }
    )
    writes = StorageWriteResults()
    deletes = StorageDeleteResults(
        {
            "missing": StorageDeleteResult(
                key="missing", status=StorageOperationStatus.NOT_FOUND
            )
        }
    )

    assert reads.get_value("missing") is None
    assert not writes
    deletes.assert_succeeded(["missing"], allow_not_found=True)
    with pytest.raises(RuntimeError, match='status "missing"'):
        writes.assert_succeeded(["missing"])

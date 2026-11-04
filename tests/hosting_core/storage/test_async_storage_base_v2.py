# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.core.storage import (
    AsyncStorageBaseV2,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageDeleteResults,
    StorageOperationStatus,
    StorageReadResult,
    StorageReadResults,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
    StorageWriteResults,
)
from tests._common.storage.utils import MockStoreItem


class _RecordingStorageV2(AsyncStorageBaseV2):
    def __init__(self) -> None:
        self.initialize_count = 0
        self.read_calls = []
        self.write_calls = []
        self.delete_calls = []

    async def initialize(self) -> None:
        self.initialize_count += 1

    async def _read_item(self, key, *, target_cls, **kwargs):
        self.read_calls.append((key, target_cls, kwargs))
        return StorageReadResult(
            key=key,
            status=StorageOperationStatus.SUCCEEDED,
            value=target_cls({"key": key}),
            version=f"version-{key}",
        )

    async def _write_item(self, key, value, options):
        self.write_calls.append((key, value, options))
        return StorageWriteResult(
            key=key,
            status=StorageOperationStatus.SUCCEEDED,
            version=f"version-{key}",
        )

    async def _delete_item(self, key, options):
        self.delete_calls.append((key, options))
        return StorageDeleteResult(
            key=key,
            status=StorageOperationStatus.SUCCEEDED,
        )


@pytest.mark.asyncio
async def test_base_builds_v2_bulk_operations_from_single_item_hooks():
    storage = _RecordingStorageV2()
    write_options = StorageWriteOptions(mode=StorageWriteMode.CREATE_ONLY)
    delete_options = StorageDeleteOptions(expected_version="version-a")
    values = {"a": MockStoreItem(), "b": MockStoreItem()}

    reads = await storage.read(
        ["a", "b"], target_cls=MockStoreItem, custom_argument=True
    )
    writes = await storage.write(values, write_options)
    deletes = await storage.delete(["a", "b"], delete_options)

    assert isinstance(reads, StorageReadResults)
    assert isinstance(writes, StorageWriteResults)
    assert isinstance(deletes, StorageDeleteResults)
    assert list(reads) == ["a", "b"]
    assert list(writes) == ["a", "b"]
    assert list(deletes) == ["a", "b"]
    assert storage.initialize_count == 3
    assert storage.read_calls == [
        ("a", MockStoreItem, {"custom_argument": True}),
        ("b", MockStoreItem, {"custom_argument": True}),
    ]
    assert storage.write_calls == [
        ("a", values["a"], write_options),
        ("b", values["b"], write_options),
    ]
    assert storage.delete_calls == [
        ("a", delete_options),
        ("b", delete_options),
    ]


@pytest.mark.asyncio
async def test_base_returns_empty_results_without_initializing():
    storage = _RecordingStorageV2()

    reads = await storage.read([], target_cls=MockStoreItem)
    writes = await storage.write({})
    deletes = await storage.delete([])

    assert isinstance(reads, StorageReadResults)
    assert isinstance(writes, StorageWriteResults)
    assert isinstance(deletes, StorageDeleteResults)
    assert not reads
    assert not writes
    assert not deletes
    assert storage.initialize_count == 0


@pytest.mark.asyncio
async def test_base_validates_v2_inputs_before_initializing():
    storage = _RecordingStorageV2()

    with pytest.raises(ValueError, match="keys must be non-empty"):
        await storage.read([" "], target_cls=MockStoreItem)
    with pytest.raises(ValueError, match="values must implement"):
        await storage.write({"key": object()})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="expected_version cannot be empty"):
        await storage.delete(["key"], StorageDeleteOptions(expected_version=""))

    assert storage.initialize_count == 0

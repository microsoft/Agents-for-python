# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from asyncio import Lock
from copy import deepcopy
from typing import TypeVar, cast

from ._type_aliases import JSON
from .storage import (
    Storage,
    StorageDeleteOptions,
    StorageDeleteResult,
    StorageDeleteResults,
    StorageOperationStatus,
    StorageReadResult,
    StorageReadResults,
    StorageV2,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
    StorageWriteResults,
    is_store_item,
)
from .storage_compatibility import (
    validate_expected_version,
    validate_storage_v2_changes,
    validate_storage_v2_keys,
)
from .store_item import StoreItem
from .telemetry import spans

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class _MemoryStore:
    """Shared synchronized persistence mechanics for the two public adapters."""

    def __init__(self, state: dict[str, JSON] | None = None) -> None:
        self._memory: dict[str, JSON] = state or {}
        self._versions: dict[str, str] = {}
        self._next_version = 1
        self._lock = Lock()

    async def read(
        self,
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        copy_data: bool,
    ) -> StorageReadResults[StoreItemT]:
        results: StorageReadResults[StoreItemT] = StorageReadResults()
        async with self._lock:
            for key in keys:
                if key not in self._memory:
                    results[key] = cast(
                        StorageReadResult[StoreItemT],
                        StorageReadResult(
                            key=key, status=StorageOperationStatus.NOT_FOUND
                        ),
                    )
                    continue
                data = self._memory[key]
                if copy_data:
                    data = deepcopy(data)
                results[key] = cast(
                    StorageReadResult[StoreItemT],
                    StorageReadResult(
                        key=key,
                        status=StorageOperationStatus.SUCCEEDED,
                        value=cast(
                            StoreItemT, target_cls.from_json_to_store_item(data)
                        ),
                        version=self._versions.get(key),
                    ),
                )
        return results

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions,
        *,
        copy_data: bool,
    ) -> StorageWriteResults:
        results = StorageWriteResults()
        async with self._lock:
            for key, value in changes.items():
                exists = key in self._memory
                current_version = self._versions.get(key)
                if options.mode == StorageWriteMode.CREATE_ONLY and exists:
                    results[key] = StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONFLICT,
                        version=current_version,
                    )
                    continue
                if (
                    options.expected_version is not None
                    and options.expected_version != current_version
                ):
                    results[key] = StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=current_version,
                    )
                    continue
                if options.mode == StorageWriteMode.REPLACE and not exists:
                    results[key] = StorageWriteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                    continue

                data = value.store_item_to_json()
                self._memory[key] = deepcopy(data) if copy_data else data
                version = self._new_version()
                self._versions[key] = version
                results[key] = StorageWriteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=version,
                )
        return results

    async def delete(
        self, keys: list[str], options: StorageDeleteOptions
    ) -> StorageDeleteResults:
        results = StorageDeleteResults()
        async with self._lock:
            for key in keys:
                if key not in self._memory:
                    status = (
                        StorageOperationStatus.CONDITION_NOT_MET
                        if options.expected_version is not None
                        else StorageOperationStatus.NOT_FOUND
                    )
                    results[key] = StorageDeleteResult(key=key, status=status)
                    continue
                current_version = self._versions.get(key)
                if (
                    options.expected_version is not None
                    and options.expected_version != current_version
                ):
                    results[key] = StorageDeleteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=current_version,
                    )
                    continue
                self._memory.pop(key)
                self._versions.pop(key, None)
                results[key] = StorageDeleteResult(
                    key=key,
                    status=StorageOperationStatus.SUCCEEDED,
                    version=current_version,
                )
        return results

    def _new_version(self) -> str:
        version = str(self._next_version)
        self._next_version += 1
        return version


class MemoryStorage(Storage):
    """Legacy in-memory storage adapter for testing and development."""

    def __init__(self, state: dict[str, JSON] | None = None) -> None:
        self._store = _MemoryStore(state)

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs: object
    ) -> dict[str, StoreItemT]:
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")
        if any(not key for key in keys):
            raise ValueError("MemoryStorage.read(): key cannot be empty")
        with spans.StorageRead(len(keys)):
            results = await self._store.read(
                keys, target_cls=target_cls, copy_data=False
            )
        return {
            key: value for key in keys if (value := results.get_value(key)) is not None
        }

    async def write(self, changes: dict[str, StoreItem]) -> None:
        if not changes:
            raise ValueError("MemoryStorage.write(): changes cannot be empty")
        if any(not key for key in changes):
            raise ValueError("MemoryStorage.write(): key cannot be empty")
        with spans.StorageWrite(len(changes)):
            results = await self._store.write(
                changes, StorageWriteOptions(), copy_data=False
            )
        results.assert_succeeded(changes)

    async def delete(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")
        if any(not key for key in keys):
            raise ValueError("MemoryStorage.delete(): key cannot be empty")
        with spans.StorageDelete(len(keys)):
            results = await self._store.delete(keys, StorageDeleteOptions())
        results.assert_succeeded(keys, allow_not_found=True)


class MemoryStorageV2(StorageV2):
    """In-memory Storage V2 adapter with per-key results and versions."""

    def __init__(self, state: dict[str, JSON] | None = None) -> None:
        self._store = _MemoryStore(state)

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs: object
    ) -> StorageReadResults[StoreItemT]:
        validate_storage_v2_keys(keys)
        with spans.StorageRead(len(keys)):
            return await self._store.read(keys, target_cls=target_cls, copy_data=True)

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults:
        validate_storage_v2_changes(changes)
        write_options = options or StorageWriteOptions()
        validate_expected_version(write_options.expected_version)
        if any(not is_store_item(value) for value in changes.values()):
            raise ValueError("Storage V2 values must implement store_item_to_json().")
        with spans.StorageWrite(len(changes)):
            return await self._store.write(changes, write_options, copy_data=True)

    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults:
        validate_storage_v2_keys(keys)
        delete_options = options or StorageDeleteOptions()
        validate_expected_version(delete_options.expected_version)
        with spans.StorageDelete(len(keys)):
            return await self._store.delete(keys, delete_options)

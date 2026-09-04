# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Compatibility helpers for Storage V1 and Storage V2."""

from __future__ import annotations

from collections.abc import Mapping

from .storage import (
    Storage,
    StorageDeleteOptions,
    StorageDeleteResults,
    StorageDeleteResult,
    StorageOperationStatus,
    StorageProvider,
    StoreItemT,
    StorageReadResult,
    StorageReadResults,
    StorageV2,
    StorageVersion,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResults,
    StorageWriteResult,
)
from .store_item import StoreItem


def is_storage_v2(storage: StorageProvider) -> bool:
    """Return ``True`` only for a provider that implements the V2 interface."""
    return isinstance(storage, StorageV2) and (
        storage.storage_version == StorageVersion.V2
    )


def as_storage_v2(storage: StorageProvider) -> StorageV2:
    """Convert a supported provider to the V2 interface."""
    if isinstance(storage, _StorageV2ToStorageAdapter):
        return storage.source
    if is_storage_v2(storage):
        return storage
    return _StorageToStorageV2Adapter(storage)


def as_storage(storage: StorageProvider) -> Storage:
    """Convert a supported provider to the legacy V1 interface."""
    if is_storage_v2(storage):
        return _StorageV2ToStorageAdapter(storage)
    return storage


def get_storage_read_value(
    results: StorageReadResults[StoreItemT] | None, key: str
) -> StoreItemT | None:
    """Return a successful V2 value, map not-found to ``None``, or raise."""
    result = results.get(key) if results is not None else None
    if result is not None and result.status == StorageOperationStatus.NOT_FOUND:
        return None
    if result is not None and result.status == StorageOperationStatus.SUCCEEDED:
        return result.value
    _raise_result_error("read", key, result.status if result else None)


def assert_storage_write_succeeded(
    results: StorageWriteResults | None, keys: list[str]
) -> None:
    """Raise unless every V2 write result succeeded."""
    _assert_results("write", results, keys, {StorageOperationStatus.SUCCEEDED})


def assert_storage_delete_succeeded(
    results: StorageDeleteResults | None, keys: list[str]
) -> None:
    """Raise unless every V2 delete kept V1 idempotent semantics."""
    _assert_results(
        "delete",
        results,
        keys,
        {StorageOperationStatus.SUCCEEDED, StorageOperationStatus.NOT_FOUND},
    )


def validate_storage_v2_keys(keys: list[str]) -> None:
    """Validate V2 key input."""
    if not isinstance(keys, list):
        raise ValueError("Storage V2 keys must be a list.")
    if any(not isinstance(key, str) or not key.strip() for key in keys):
        raise ValueError("Storage V2 keys must be non-empty strings.")


def validate_storage_v2_changes(changes: Mapping[str, object]) -> None:
    """Validate V2 change keys."""
    if not isinstance(changes, dict):
        raise ValueError("Storage V2 changes must be a dictionary.")
    if any(not isinstance(key, str) or not key.strip() for key in changes):
        raise ValueError("Storage V2 keys must be non-empty strings.")


def validate_expected_version(expected_version: str | None) -> None:
    """Validate an optional V2 version token."""
    if expected_version == "":
        raise ValueError("Storage V2 expected_version cannot be empty.")


def validate_write_mode(mode: StorageWriteMode) -> None:
    """Validate a V2 write mode."""
    if not isinstance(mode, StorageWriteMode):
        raise ValueError(f'Storage V2 write mode "{mode}" is not supported.')


class _StorageV2ToStorageAdapter(Storage):
    """Adapt V2 storage for V1 consumers."""

    def __init__(self, storage: StorageV2):
        self._storage = storage

    @property
    def source(self) -> StorageV2:
        """Return the unwrapped V2 provider."""
        return self._storage

    async def read(self, keys, *, target_cls, **kwargs):
        results = await self._storage.read(keys, target_cls=target_cls, **kwargs)
        values: dict[str, StoreItem] = {}
        for key in keys:
            value = get_storage_read_value(results, key)
            if value is not None:
                values[key] = value
        return values

    async def write(self, changes: dict[str, StoreItem]) -> None:
        results = await self._storage.write(changes)
        assert_storage_write_succeeded(results, list(changes))

    async def delete(self, keys: list[str]) -> None:
        results = await self._storage.delete(keys)
        assert_storage_delete_succeeded(results, keys)


class _StorageToStorageV2Adapter(StorageV2):
    """Adapt a legacy provider where V2 behavior is safely available."""

    storage_version = StorageVersion.V2

    def __init__(self, storage: Storage):
        self._storage = storage

    async def read(self, keys, *, target_cls, **kwargs):
        validate_storage_v2_keys(keys)
        if not keys:
            return {}
        items = await self._storage.read(keys, target_cls=target_cls, **kwargs)
        return {
            key: StorageReadResult(
                key=key,
                status=(
                    StorageOperationStatus.SUCCEEDED
                    if key in items
                    else StorageOperationStatus.NOT_FOUND
                ),
                value=items.get(key),
            )
            for key in keys
        }

    async def write(self, changes, options=None):
        validate_storage_v2_changes(changes)
        if not changes:
            return {}
        options = options or StorageWriteOptions()
        validate_write_mode(options.mode)
        validate_expected_version(options.expected_version)
        if options.mode != StorageWriteMode.UPSERT:
            raise NotImplementedError(
                'Legacy storage does not support the V2 storage option "mode".'
            )
        if options.expected_version is not None:
            raise NotImplementedError(
                "Legacy storage does not support the V2 storage option "
                '"expected_version".'
            )
        await self._storage.write(changes)
        return {
            key: StorageWriteResult(key=key, status=StorageOperationStatus.SUCCEEDED)
            for key in changes
        }

    async def delete(self, keys, options=None):
        validate_storage_v2_keys(keys)
        if not keys:
            return {}
        options = options or StorageDeleteOptions()
        validate_expected_version(options.expected_version)
        if options.expected_version is not None:
            raise NotImplementedError(
                "Legacy storage does not support the V2 storage option "
                '"expected_version".'
            )
        await self._storage.delete(keys)
        return {
            key: StorageDeleteResult(key=key, status=StorageOperationStatus.SUCCEEDED)
            for key in keys
        }


def _assert_results(operation, results, keys, accepted_statuses) -> None:
    for key in keys:
        result = results.get(key) if results is not None else None
        if result is None or result.status not in accepted_statuses:
            _raise_result_error(
                operation, key, result.status if result is not None else None
            )


def _raise_result_error(
    operation: str, key: str, status: StorageOperationStatus | None
):
    value = status.value if status is not None else "missing"
    raise RuntimeError(
        f'Storage V2 {operation} failed for key "{key}" with status "{value}".'
    )

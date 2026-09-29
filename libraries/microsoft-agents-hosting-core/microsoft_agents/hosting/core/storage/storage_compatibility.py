# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Compatibility helpers for Storage V1 and Storage V2."""

from __future__ import annotations

from typing import Any, NoReturn

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
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResults,
    StorageWriteResult,
)
from .store_item import StoreItem


def is_storage_v2(storage: StorageProvider) -> bool:
    """Return ``True`` only for a provider that implements the V2 interface."""
    return isinstance(storage, StorageV2)


def as_storage_v2(storage: StorageProvider) -> StorageV2:
    """Convert a supported provider to the V2 interface."""
    if is_storage_v2(storage):
        return storage
    return _StorageToStorageV2Adapter(storage)


def get_storage_read_value(
    results: StorageReadResults[StoreItemT] | None, key: str
) -> StoreItemT | None:
    """Return a successful V2 value, map not-found to ``None``, or raise."""
    if results is None:
        _raise_result_error("read", key, None)
    return results.get_value(key)


def assert_storage_write_succeeded(
    results: StorageWriteResults | None, keys: list[str]
) -> None:
    """Raise unless every V2 write result succeeded."""
    if results is None:
        _raise_result_error("write", keys[0] if keys else "", None)
    results.assert_succeeded(keys)


def assert_storage_delete_succeeded(
    results: StorageDeleteResults | None, keys: list[str]
) -> None:
    """Raise unless every V2 delete kept V1 idempotent semantics."""
    if results is None:
        _raise_result_error("delete", keys[0] if keys else "", None)
    results.assert_succeeded(keys, allow_not_found=True)


def validate_storage_v2_keys(keys: list[str]) -> None:
    """Validate V2 key input."""
    if any(not key.strip() for key in keys):
        raise ValueError("Storage V2 keys must be non-empty strings.")


def validate_storage_v2_changes(changes: dict[str, object]) -> None:
    """Validate V2 change keys."""
    if any(not key.strip() for key in changes):
        raise ValueError("Storage V2 keys must be non-empty strings.")


def validate_expected_version(expected_version: str | None) -> None:
    """Validate an optional V2 version token."""
    if expected_version == "":
        raise ValueError("Storage V2 expected_version cannot be empty.")


class _StorageToStorageV2Adapter(StorageV2):
    """Adapt a legacy provider where V2 behavior is safely available."""

    def __init__(self, storage: Storage):
        self._storage = storage

    async def read(
        self,
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs: Any,
    ) -> StorageReadResults[StoreItemT]:
        validate_storage_v2_keys(keys)
        if not keys:
            return StorageReadResults()
        items = await self._storage.read(keys, target_cls=target_cls, **kwargs)
        return StorageReadResults(
            {
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
        )

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults:
        validate_storage_v2_changes(changes)
        if not changes:
            return StorageWriteResults()
        options = options or StorageWriteOptions()
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
        return StorageWriteResults(
            {
                key: StorageWriteResult(
                    key=key, status=StorageOperationStatus.SUCCEEDED
                )
                for key in changes
            }
        )

    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults:
        validate_storage_v2_keys(keys)
        if not keys:
            return StorageDeleteResults()
        options = options or StorageDeleteOptions()
        validate_expected_version(options.expected_version)
        if options.expected_version is not None:
            raise NotImplementedError(
                "Legacy storage does not support the V2 storage option "
                '"expected_version".'
            )
        await self._storage.delete(keys)
        return StorageDeleteResults(
            {
                key: StorageDeleteResult(
                    key=key, status=StorageOperationStatus.SUCCEEDED
                )
                for key in keys
            }
        )


def _raise_result_error(
    operation: str, key: str, status: StorageOperationStatus | None
) -> NoReturn:
    value = status.value if status is not None else "missing"
    raise RuntimeError(
        f'Storage V2 {operation} failed for key "{key}" with status "{value}".'
    )

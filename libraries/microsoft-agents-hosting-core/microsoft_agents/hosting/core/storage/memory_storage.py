# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from asyncio import Lock
from copy import deepcopy
from typing import Generic, Literal, TypeVar, cast, overload

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
    StorageVersion,
    StorageVersionT,
    StorageWriteMode,
    StorageWriteOptions,
    StorageWriteResult,
    StorageWriteResults,
    is_store_item,
)
from .store_item import StoreItem
from .storage_compatibility import (
    validate_expected_version,
    validate_storage_v2_changes,
    validate_storage_v2_keys,
    validate_write_mode,
)
from .telemetry import spans

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class MemoryStorage(Storage, StorageV2, Generic[StorageVersionT]):
    """In-memory storage implementation for testing and development purposes."""

    def __init__(
        self,
        state: dict[str, JSON] | None = None,
        *,
        storage_version: StorageVersionT = StorageVersion.V1,
    ):
        """Initializes the MemoryStorage with an optional initial state.

        :param state: An optional dictionary representing the initial state of the storage.
        :raises ValueError: If state is not a dictionary or None.
        """
        if storage_version not in (StorageVersion.V1, StorageVersion.V2):
            raise ValueError(f'Storage version "{storage_version}" is not supported.')
        self.storage_version = StorageVersion(storage_version)
        self._memory: dict[str, JSON] = state or {}
        self._versions: dict[str, str] = {}
        self._next_version = 1
        self._lock = Lock()

    @overload
    async def read(
        self: "MemoryStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> dict[str, StoreItemT]: ...

    @overload
    async def read(
        self: "MemoryStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> StorageReadResults[StoreItemT]: ...

    @overload
    async def read(
        self: "MemoryStorage[StorageVersion]",
        keys: list[str],
        *,
        target_cls: type[StoreItemT],
        **kwargs,
    ) -> dict[str, StoreItemT] | StorageReadResults[StoreItemT]: ...

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> dict[str, StoreItemT] | StorageReadResults[StoreItemT]:
        """Reads items from the in-memory storage.

        :param keys: A list of keys to read from the storage.
        :param target_cls: The class type of the items to be read. Must be a subclass of StoreItem.
        :return: A dictionary mapping keys to their corresponding StoreItem instances.
        :raises ValueError: If keys are empty.
        """

        with spans.StorageRead(len(keys) if isinstance(keys, list) else 0):
            if self.storage_version == StorageVersion.V2:
                return await self._read_v2(keys, target_cls=target_cls)
            return await self._read_v1(keys, target_cls=target_cls)

    @overload
    async def write(
        self: "MemoryStorage[Literal[StorageVersion.V1]]",
        changes: dict[str, StoreItem],
        options: None = None,
    ) -> None: ...

    @overload
    async def write(
        self: "MemoryStorage[Literal[StorageVersion.V2]]",
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults: ...

    @overload
    async def write(
        self: "MemoryStorage[StorageVersion]",
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> None | StorageWriteResults: ...

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> None | StorageWriteResults:
        """Writes items to the in-memory storage.

        :param changes: A dictionary mapping keys to StoreItem instances to be written to the storage.
        :raises ValueError: If changes is None or any key is empty.
        """
        with spans.StorageWrite(len(changes) if isinstance(changes, dict) else 0):
            if self.storage_version == StorageVersion.V2:
                return await self._write_v2(changes, options)
            return await self._write_v1(changes)

    @overload
    async def delete(
        self: "MemoryStorage[Literal[StorageVersion.V1]]",
        keys: list[str],
        options: None = None,
    ) -> None: ...

    @overload
    async def delete(
        self: "MemoryStorage[Literal[StorageVersion.V2]]",
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults: ...

    @overload
    async def delete(
        self: "MemoryStorage[StorageVersion]",
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> None | StorageDeleteResults: ...

    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> None | StorageDeleteResults:
        """Deletes items from the in-memory storage.

        :param keys: A list of keys to delete from the storage.
        :raises ValueError: If keys is empty or any key is empty.
        """

        with spans.StorageDelete(len(keys) if isinstance(keys, list) else 0):
            if self.storage_version == StorageVersion.V2:
                return await self._delete_v2(keys, options)
            return await self._delete_v1(keys)

    async def _read_v1(
        self, keys: list[str], *, target_cls: type[StoreItemT]
    ) -> dict[str, StoreItemT]:
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")

        result: dict[str, StoreItemT] = {}
        async with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.read(): key cannot be empty")
                if key in self._memory:
                    result[key] = cast(
                        StoreItemT,
                        target_cls.from_json_to_store_item(self._memory[key]),
                    )
        return result

    async def _write_v1(self, changes: dict[str, StoreItem]) -> None:
        if not changes:
            raise ValueError("MemoryStorage.write(): changes cannot be None")

        async with self._lock:
            for key in changes:
                if key == "":
                    raise ValueError("MemoryStorage.write(): key cannot be empty")
                self._memory[key] = changes[key].store_item_to_json()

    async def _delete_v1(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        async with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.delete(): key cannot be empty")
                self._memory.pop(key, None)

    async def _read_v2(
        self, keys: list[str], *, target_cls: type[StoreItemT]
    ) -> StorageReadResults[StoreItemT]:
        validate_storage_v2_keys(keys)
        async with self._lock:
            results: StorageReadResults[StoreItemT] = {}
            for key in keys:
                if key not in self._memory:
                    results[key] = cast(
                        StorageReadResult[StoreItemT],
                        StorageReadResult(
                            key=key, status=StorageOperationStatus.NOT_FOUND
                        ),
                    )
                    continue
                results[key] = cast(
                    StorageReadResult[StoreItemT],
                    StorageReadResult(
                        key=key,
                        status=StorageOperationStatus.SUCCEEDED,
                        value=cast(
                            StoreItemT,
                            target_cls.from_json_to_store_item(
                                deepcopy(self._memory[key])
                            ),
                        ),
                        version=self._versions.get(key),
                    ),
                )
            return results

    async def _write_v2(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None,
    ) -> StorageWriteResults:
        validate_storage_v2_changes(changes)
        if not changes:
            return {}
        options = options or StorageWriteOptions()
        validate_write_mode(options.mode)
        validate_expected_version(options.expected_version)
        if any(not is_store_item(value) for value in changes.values()):
            raise ValueError("Storage V2 values must implement store_item_to_json().")

        async with self._lock:
            results: StorageWriteResults = {}
            for key, value in changes.items():
                exists = key in self._memory
                current_version = self._versions.get(key)
                if options.mode == StorageWriteMode.CREATE_ONLY and exists:
                    results[key] = StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONFLICT,
                        version=current_version,
                    )
                elif options.mode == StorageWriteMode.REPLACE and not exists:
                    results[key] = StorageWriteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
                elif (
                    options.expected_version is not None
                    and options.expected_version != current_version
                ):
                    results[key] = StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.CONDITION_NOT_MET,
                        version=current_version,
                    )
                else:
                    version = self._new_version()
                    self._memory[key] = deepcopy(value.store_item_to_json())
                    self._versions[key] = version
                    results[key] = StorageWriteResult(
                        key=key,
                        status=StorageOperationStatus.SUCCEEDED,
                        version=version,
                    )
            return results

    async def _delete_v2(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None,
    ) -> StorageDeleteResults:
        validate_storage_v2_keys(keys)
        options = options or StorageDeleteOptions()
        validate_expected_version(options.expected_version)

        async with self._lock:
            results: StorageDeleteResults = {}
            for key in keys:
                if key not in self._memory:
                    results[key] = StorageDeleteResult(
                        key=key, status=StorageOperationStatus.NOT_FOUND
                    )
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

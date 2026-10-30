# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from enum import Enum
from collections.abc import Iterable
from typing import Generic, NoReturn, TypeAlias, TypeVar
from abc import ABC, abstractmethod
from asyncio import gather

from .store_item import StoreItem
from .telemetry import spans

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class StorageOperationStatus(str, Enum):
    """Outcome of one version 2 storage operation."""

    SUCCEEDED = "succeeded"
    NOT_FOUND = "notFound"
    CONFLICT = "conflict"
    CONDITION_NOT_MET = "conditionNotMet"


class StorageWriteMode(str, Enum):
    """Write mode for a version 2 storage operation."""

    UPSERT = "upsert"
    CREATE_ONLY = "createOnly"
    REPLACE = "replace"


def is_store_item(value: object) -> bool:
    """Return whether a value can be serialized by a storage provider."""
    return callable(getattr(value, "store_item_to_json", None))


@dataclass(frozen=True, slots=True)
class StorageWriteOptions:
    """Options applied to every item in a version 2 write operation."""

    mode: StorageWriteMode = StorageWriteMode.UPSERT
    expected_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, StorageWriteMode):
            raise ValueError(f'Storage V2 write mode "{self.mode}" is not supported.')


@dataclass(frozen=True, slots=True)
class StorageDeleteOptions:
    """Options applied to every item in a version 2 delete operation."""

    expected_version: str | None = None


@dataclass(frozen=True, slots=True)
class StorageReadResult(Generic[StoreItemT]):
    """Result for one version 2 read operation."""

    key: str
    status: StorageOperationStatus
    value: StoreItemT | None = None
    version: str | None = None


@dataclass(frozen=True, slots=True)
class StorageWriteResult:
    """Result for one version 2 write operation."""

    key: str
    status: StorageOperationStatus
    version: str | None = None


@dataclass(frozen=True, slots=True)
class StorageDeleteResult:
    """Result for one version 2 delete operation."""

    key: str
    status: StorageOperationStatus
    version: str | None = None


def _raise_result_error(
    operation: str, key: str, status: StorageOperationStatus | None
) -> NoReturn:
    value = status.value if status is not None else "missing"
    raise RuntimeError(
        f'Storage V2 {operation} failed for key "{key}" with status "{value}".'
    )


class StorageReadResults(dict[str, StorageReadResult[StoreItemT]], Generic[StoreItemT]):
    """Per-key results returned by a Storage V2 read operation."""

    def get_value(self, key: str) -> StoreItemT | None:
        """Return a successful value, map not-found to ``None``, or raise."""
        result = self.get(key)
        if result is not None and result.status == StorageOperationStatus.NOT_FOUND:
            return None
        if result is not None and result.status == StorageOperationStatus.SUCCEEDED:
            return result.value
        _raise_result_error("read", key, result.status if result else None)


class StorageWriteResults(dict[str, StorageWriteResult]):
    """Per-key results returned by a Storage V2 write operation."""

    def assert_succeeded(self, keys: Iterable[str] | None = None) -> None:
        """Raise unless every requested write succeeded."""
        for key in keys if keys is not None else self:
            result = self.get(key)
            if result is None or result.status != StorageOperationStatus.SUCCEEDED:
                _raise_result_error(
                    "write", key, result.status if result is not None else None
                )


class StorageDeleteResults(dict[str, StorageDeleteResult]):
    """Per-key results returned by a Storage V2 delete operation."""

    def assert_succeeded(
        self,
        keys: Iterable[str] | None = None,
        *,
        allow_not_found: bool = False,
    ) -> None:
        """Raise unless every requested delete has an accepted outcome."""
        accepted = {StorageOperationStatus.SUCCEEDED}
        if allow_not_found:
            accepted.add(StorageOperationStatus.NOT_FOUND)
        for key in keys if keys is not None else self:
            result = self.get(key)
            if result is None or result.status not in accepted:
                _raise_result_error(
                    "delete", key, result.status if result is not None else None
                )


class Storage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> dict[str, StoreItemT]:
        """Reads multiple items from storage.

        :param keys: A list of keys to read.
        :param target_cls: The class of the StoreItem to deserialize the data into.
        :return: A dictionary of key to StoreItem.
        """
        pass

    @abstractmethod
    async def write(self, changes: dict[str, StoreItem]) -> None:
        """Writes multiple items to storage.

        :param changes: A dictionary of key to StoreItem to write.
        """
        pass

    @abstractmethod
    async def delete(self, keys: list[str]) -> None:
        """Deletes multiple items from storage.

        If a key does not exist, it is ignored.

        keys: A list of keys to delete.
        """
        pass


class StorageV2(ABC):
    """Version 2 storage interface.

    Each operation returns a result for every requested key. Values remain
    :class:`StoreItem` instances because the Python SDK requires an explicit
    deserialization type for reads.
    """

    @abstractmethod
    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> StorageReadResults[StoreItemT]:
        """Reads items and returns one result per requested key."""
        pass

    @abstractmethod
    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults:
        """Writes items and returns one result per requested key."""
        pass

    @abstractmethod
    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults:
        """Deletes items and returns one result per requested key."""
        pass


StorageProvider: TypeAlias = Storage | StorageV2


class AsyncStorageBase(Storage):
    """Base class for asynchronous storage implementations with operations
    that work on single items. The bulk operations are implemented in terms
    of the single-item operations.
    """

    async def initialize(self) -> None:
        """Initializes the storage container"""
        pass

    @abstractmethod
    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> tuple[str | None, StoreItemT | None]:
        """Reads a single item from storage by key.

        :param key: The key to read.
        :param target_cls: The class of the StoreItem to deserialize the data into.
        :return: A tuple of key and StoreItem. If the item does not exist, returns (None, None).
        """
        pass

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> dict[str, StoreItemT]:
        """
        Reads multiple items from storage.

        :param keys: A list of keys to read.
        :param target_cls: The class of the StoreItem to deserialize the data into.
        :return: A dictionary of key to StoreItem.
        :raises ValueError: If keys is empty.
        """
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")

        with spans.StorageRead(len(keys)):
            await self.initialize()

            items: list[tuple[str | None, StoreItemT | None]] = await gather(
                *[self._read_item(key, target_cls=target_cls, **kwargs) for key in keys]
            )
            return {
                key: value
                for key, value in items
                if key is not None and value is not None
            }

    @abstractmethod
    async def _write_item(self, key: str, value: StoreItem) -> None:
        """Writes a single item to storage by key."""
        pass

    async def write(self, changes: dict[str, StoreItem]) -> None:
        """Writes multiple items to storage.

        :param changes: A dictionary of key to StoreItem to write.
        :raises ValueError: If changes is empty.
        """
        if not changes:
            raise ValueError("Storage.write(): Changes are required when writing.")

        with spans.StorageWrite(len(changes)):
            await self.initialize()

            await gather(
                *[self._write_item(key, value) for key, value in changes.items()]
            )

    @abstractmethod
    async def _delete_item(self, key: str) -> None:
        """Deletes a single item from storage by key.

        :param key: The key to delete.
        """
        pass

    async def delete(self, keys: list[str]) -> None:
        """Deletes multiple items from storage.

        :param keys: A list of keys to delete.
        :raises ValueError: If keys is empty.
        """
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        with spans.StorageDelete(len(keys)):
            await self.initialize()

            await gather(*[self._delete_item(key) for key in keys])


class AsyncStorageBaseV2(StorageV2):
    """Build V2 bulk operations from provider-specific single-item operations."""

    async def initialize(self) -> None:
        """Initialize the backing storage when required by the provider."""
        pass

    @abstractmethod
    async def _read_item(
        self, key: str, *, target_cls: type[StoreItemT], **kwargs
    ) -> StorageReadResult[StoreItemT]:
        """Read one item and return its result."""
        pass

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> StorageReadResults[StoreItemT]:
        if any(not key.strip() for key in keys):
            raise ValueError("Storage V2 keys must be non-empty strings.")
        if not keys:
            return StorageReadResults()
        with spans.StorageRead(len(keys)):
            await self.initialize()
            results = await gather(
                *(self._read_item(key, target_cls=target_cls, **kwargs) for key in keys)
            )
        return StorageReadResults((result.key, result) for result in results)

    @abstractmethod
    async def _write_item(
        self, key: str, value: StoreItem, options: StorageWriteOptions
    ) -> StorageWriteResult:
        """Write one item and return its result."""
        pass

    async def write(
        self,
        changes: dict[str, StoreItem],
        options: StorageWriteOptions | None = None,
    ) -> StorageWriteResults:
        if any(not key.strip() for key in changes):
            raise ValueError("Storage V2 keys must be non-empty strings.")
        if not changes:
            return StorageWriteResults()
        if any(not is_store_item(value) for value in changes.values()):
            raise ValueError("Storage V2 values must implement store_item_to_json().")
        write_options = options or StorageWriteOptions()
        if write_options.expected_version == "":
            raise ValueError("Storage V2 expected_version cannot be empty.")
        with spans.StorageWrite(len(changes)):
            await self.initialize()
            results = await gather(
                *(
                    self._write_item(key, value, write_options)
                    for key, value in changes.items()
                )
            )
        return StorageWriteResults((result.key, result) for result in results)

    @abstractmethod
    async def _delete_item(
        self, key: str, options: StorageDeleteOptions
    ) -> StorageDeleteResult:
        """Delete one item and return its result."""
        pass

    async def delete(
        self,
        keys: list[str],
        options: StorageDeleteOptions | None = None,
    ) -> StorageDeleteResults:
        if any(not key.strip() for key in keys):
            raise ValueError("Storage V2 keys must be non-empty strings.")
        if not keys:
            return StorageDeleteResults()
        delete_options = options or StorageDeleteOptions()
        if delete_options.expected_version == "":
            raise ValueError("Storage V2 expected_version cannot be empty.")
        with spans.StorageDelete(len(keys)):
            await self.initialize()
            results = await gather(
                *(self._delete_item(key, delete_options) for key in keys)
            )
        return StorageDeleteResults((result.key, result) for result in results)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Generic, Literal, TypeAlias
from abc import ABC, abstractmethod
from asyncio import gather
from typing_extensions import TypeVar

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


class StorageVersion(IntEnum):
    """Supported storage contract versions."""

    V1 = 1
    V2 = 2


StorageVersionT = TypeVar(
    "StorageVersionT",
    Literal[StorageVersion.V1],
    Literal[StorageVersion.V2],
    StorageVersion,
    default=Literal[StorageVersion.V1],
)


def is_store_item(value: object) -> bool:
    """Return whether a value can be serialized by a storage provider."""
    return callable(getattr(value, "store_item_to_json", None))


@dataclass(frozen=True, slots=True)
class StorageWriteOptions:
    """Options applied to every item in a version 2 write operation."""

    mode: StorageWriteMode = StorageWriteMode.UPSERT
    expected_version: str | None = None


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


StorageReadResults: TypeAlias = dict[str, StorageReadResult[StoreItemT]]
StorageWriteResults: TypeAlias = dict[str, StorageWriteResult]
StorageDeleteResults: TypeAlias = dict[str, StorageDeleteResult]


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

    storage_version = StorageVersion.V2

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

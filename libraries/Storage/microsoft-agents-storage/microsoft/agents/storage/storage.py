from typing import Protocol, TypeVar, Type, Union
from abc import ABC, abstractmethod
from asyncio import gather

from ._type_aliases import JSON
from .store_item import StoreItem


StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class Storage(Protocol):
    async def read(
        self, keys: list[str], *, target_cls: Type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:
        """Reads multiple items from storage.

        keys: A list of keys to read.
        target_cls: The class to deserialize the stored JSON into.
        Returns a dictionary of key to StoreItem.

        missing keys are omitted from the result.
        """
        pass

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        """Writes multiple items to storage.

        changes: A dictionary of key to StoreItem to write."""
        pass

    async def delete(self, keys: list[str]) -> None:
        """Deletes multiple items from storage.

        If a key does not exist, it is ignored.

        keys: A list of keys to delete.
        """
        pass


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
        self, key: str, *, target_cls: Type[StoreItemT] = None, **kwargs
    ) -> tuple[Union[str, None], Union[StoreItemT, None]]:
        """Reads a single item from storage by key.

        Returns a tuple of (key, StoreItem) if found, or (None, None) if not found.
        """
        pass

    async def read(
        self, keys: list[str], *, target_cls: Type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")
        if not target_cls:
            raise ValueError("Storage.read(): target_cls cannot be None.")

        await self.initialize()

        items: list[tuple[Union[str, None], Union[StoreItemT, None]]] = await gather(
            *[self._read_item(key, target_cls=target_cls, **kwargs) for key in keys]
        )
        return {key: value for key, value in items if key is not None}

    @abstractmethod
    async def _write_item(self, key: str, value: StoreItemT) -> None:
        """Writes a single item to storage by key."""
        pass

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        if not changes:
            raise ValueError("Storage.write(): Changes are required when writing.")

        await self.initialize()

        await gather(*[self._write_item(key, value) for key, value in changes.items()])

    @abstractmethod
    async def _delete_item(self, key: str) -> None:
        """Deletes a single item from storage by key."""
        pass

    async def delete(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        await self.initialize()

        await gather(*[self._delete_item(key) for key in keys])

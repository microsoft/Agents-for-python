# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from asyncio import Lock
from typing import TypeVar

from ._type_aliases import JSON
from .storage import Storage
from .store_item import StoreItem

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class MemoryStorage(Storage):
    """In-memory storage implementation for testing and development purposes."""

    def __init__(self, state: dict[str, JSON] | None = None):
        """Initializes the MemoryStorage with an optional initial state.

        :param state: An optional dictionary representing the initial state of the storage.
        :raises ValueError: If state is not a dictionary or None.
        """
        self._memory: dict[str, JSON] = state or {}
        self._lock = Lock()

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT], **kwargs
    ) -> dict[str, StoreItemT]:
        """Reads items from the in-memory storage.

        :param keys: A list of keys to read from the storage.
        :param target_cls: The class type of the items to be read. Must be a subclass of StoreItem.
        :return: A dictionary mapping keys to their corresponding StoreItem instances.
        :raises ValueError: If keys are empty or target_cls is not a subclass of StoreItem.
        """

        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")

        result: dict[str, StoreItemT] = {}
        async with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.read(): key cannot be empty")
                if key in self._memory:
                    result[key] = target_cls.from_json_to_store_item(self._memory[key])

            return result

    async def write(self, changes: dict[str, StoreItem]):
        """Writes items to the in-memory storage.

        :param changes: A dictionary mapping keys to StoreItem instances to be written to the storage.
        :raises ValueError: If changes is None or any key is empty.
        """
        if not changes:
            raise ValueError("MemoryStorage.write(): changes cannot be None")

        async with self._lock:
            for key in changes:
                if key == "":
                    raise ValueError("MemoryStorage.write(): key cannot be empty")
                self._memory[key] = changes[key].store_item_to_json()

    async def delete(self, keys: list[str]):
        """Deletes items from the in-memory storage.

        :param keys: A list of keys to delete from the storage.
        :raises ValueError: If keys is empty or any key is empty.
        """

        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        async with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.delete(): key cannot be empty")
                if key in self._memory:
                    del self._memory[key]

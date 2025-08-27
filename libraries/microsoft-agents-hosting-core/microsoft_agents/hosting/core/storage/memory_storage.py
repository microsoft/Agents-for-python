from threading import Lock
from typing import TypeVar

from ._type_aliases import JSON
from .storage import Storage
from .store_item import StoreItem


StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class MemoryStorage(Storage):
    def __init__(self, state: dict[str, JSON] = None):
        self._memory: dict[str, JSON] = state or {}
        self._lock = Lock()

    async def read(
        self, keys: list[str], *, target_cls: StoreItemT = None, **kwargs
    ) -> dict[str, StoreItemT]:

        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")
        if not target_cls:
            raise ValueError("Storage.read(): target_cls cannot be None.")

        result: dict[str, StoreItem] = {}
        with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.read(): key cannot be empty")
                if key in self._memory:
                    if not target_cls:
                        result[key] = self._memory[key]
                    else:
                        try:
                            result[key] = target_cls.from_json_to_store_item(
                                self._memory[key]
                            )
                        except AttributeError as error:
                            raise TypeError(
                                f"MemoryStorage.read(): could not deserialize in-memory item into {target_cls} class. Error: {error}"
                            )
            return result

    async def write(self, changes: dict[str, StoreItem]):
        if not changes:
            raise ValueError("MemoryStorage.write(): changes cannot be None")

        with self._lock:
            for key in changes:
                if key == "":
                    raise ValueError("MemoryStorage.write(): key cannot be empty")
                self._memory[key] = changes[key].store_item_to_json()

    async def delete(self, keys: list[str]):
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        with self._lock:
            for key in keys:
                if key == "":
                    raise ValueError("MemoryStorage.delete(): key cannot be empty")
                if key in self._memory:
                    del self._memory[key]

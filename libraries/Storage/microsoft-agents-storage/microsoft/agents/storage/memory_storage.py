from typing import Type, TypeVar
from threading import Lock

from .storage import Storage
from .store_item import StoreItem


class MemoryStorage(Storage):
    def __init__(self, state: dict[str, StoreItem] = None):
        self._memory: dict[str, StoreItem] = state or {}
        self._lock = Lock()
        self._e_tag = 0

    async def read(self, keys: list[str]) -> dict[str, StoreItem]:
        result: dict[str, StoreItem] = {}
        with self._lock:
            for key in keys:
                if key in self._memory:
                    store_item = self._memory[key]
                    if isinstance(store_item, StoreItem):
                        result[key] = store_item.from_json_to_store_item(
                            self._memory[key]
                        )
                    else:
                        raise TypeError(
                            f"MemoryStorage.read(): store_item is not of type StoreItem"
                        )
            return result

    async def write(self, changes: dict[str, StoreItem]):
        for key in changes:
            self._memory[key] = changes[key]

    async def delete(self, keys: list[str]):
        with self._lock:
            for key in keys:
                if key in self._memory:
                    del self._memory[key]

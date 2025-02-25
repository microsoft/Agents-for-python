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
        result: dict[str, StoreItem] = {}
        with self._lock:
            for key in keys:
                if key in self._memory:
                    try:
                        result[key] = target_cls.from_json_to_store_item(
                            self._memory[key]
                        )
                    except TypeError as error:
                        raise TypeError(
                            f"MemoryStorage.read(): could not deserialize in-memory item into {target_cls} class. Error: {error}"
                        )
            return result

    async def write(self, changes: dict[str, StoreItem]):
        if not changes:
            raise ValueError("MemoryStorage.write(): changes cannot be None")

        with self._lock:
            for key in changes:
                self._memory[key] = changes[key].store_item_to_json()

    async def delete(self, keys: list[str]):
        with self._lock:
            for key in keys:
                if key in self._memory:
                    del self._memory[key]

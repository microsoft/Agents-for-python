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
        self._e_tag = 0

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
                old_e_tag = self._memory.get(key, {}).get("e_tag")
                if (
                    not old_e_tag
                    or not hasattr(changes[key], "e_tag")
                    or changes[key].e_tag == "*"
                ):
                    self._e_tag += 1
                    changes[key].e_tag = self._e_tag
                elif old_e_tag != changes[key].e_tag:
                    raise ValueError(
                        f"MemoryStorage.write(): e_tag conflict.\r\n\r\nOriginal: {changes[key].e_tag}\r\nCurrent: {old_e_tag}"
                    )
                changes[key].e_tag += 1
                self._memory[key] = changes[key].store_item_to_json()

    async def delete(self, keys: list[str]):
        with self._lock:
            for key in keys:
                if key in self._memory:
                    del self._memory[key]

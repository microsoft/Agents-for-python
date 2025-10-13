from datetime import datetime, timezone
from typing import TypeVar

from ..memory_storage import MemoryStorage
from ..store_item import StoreItem

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class _DummyCache(Storage):

    async def read(self, keys: list[str], **kwargs) -> dict[str, _FlowState]:
        return {}

    async def write(self, changes: dict[str, _FlowState]) -> None:
        pass

    async def delete(self, keys: list[str]) -> None:
        pass


class _MemoryCache(MemoryStorage):
    def __init__(self, clear_interval: int = 300):
        """In-memory cache that clears itself every `clear_interval` seconds.

        :param clear_interval: Time in seconds between automatic cache clears.
            Defaults to 5 minutes.
        :type clear_interval: int
        :raises ValueError: If `clear_interval` is not positive.
        """
        if clear_interval <= 0:
            raise ValueError("clear_interval must be a positive integer.")
        self._clear_interval = clear_interval
        self._last_cleared = datetime.now(timezone.utc).timestamp()

    async def clear(self):
        """Clears the cache if the clear interval has passed."""
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            if now - self._last_cleared > self._clear_interval:
                self._memory.clear()
                self._last_cleared = now

    async def read(
        self, keys: list[str], *, target_cls: StoreItemT = None, **kwargs
    ) -> dict[str, StoreItemT]:
        self.clear()
        return await super().read(keys, target_cls=target_cls, **kwargs)

    async def write(self, changes: dict[str, StoreItem]):
        self.clear()
        return await super().write(changes)

    async def delete(self, keys: list[str]):
        self.clear()
        return await super().delete(keys)

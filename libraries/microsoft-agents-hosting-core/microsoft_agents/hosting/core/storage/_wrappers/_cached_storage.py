from typing import TypeVar, Generic

from strenum import StrEnum

from ..store_item import StoreItem
from ..storage import Storage

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class _CachedStorage(Storage):
    """Wrapper around Storage that adds a caching layer."""

    def __init__(self, storage: Storage, cache: Storage):
        """Initialize CachedStorage with a storage and cache.
        
        Args:
            storage: The backing storage.
            cache: The caching storage. This should ideally be faster or at least
                used by fewer clients than the backing storage.
        """
        self._storage = storage
        self._cache = cache

    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:

        data = await self._cache.read(keys, target_cls=target_cls, **kwargs)
        if len(data.keys()) < len(keys):
            missing_keys = [k for k in keys if k not in data]
            storage_data = await self._storage.read(
                missing_keys, target_cls=target_cls, **kwargs
            )
            if storage_data:
                await self._cache.write(storage_data)
                data.update(storage_data)
          
        return data

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        await self._cache.write(changes)
        await self._storage.write(changes)

    async def delete(self, keys: list[str]) -> None:
        await self._cache.delete(keys)
        await self._storage.delete(keys)
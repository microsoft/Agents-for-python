from typing import Generic, TypeVar, Union

from microsoft_agents.hosting.core import (
    Storage,
    StoreItem
)

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class _ItemStorage(Generic[StoreItemT]):

    def __init__(self, storage: Storage):
        self._storage = storage

    async def read(self, keys: Union[str, list[str]], **kwargs) -> dict[str, StoreItemT]:
        if isinstance(keys, str):
            keys = [keys]
        return await self._storage.read(keys, target_cls=StoreItemT, **kwargs)

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        await self._storage.write(changes)

    async def delete(self, keys: Union[str, list[str]]) -> None:
        if isinstance(keys, str):
            keys = [keys]
        await self._storage.delete(keys)

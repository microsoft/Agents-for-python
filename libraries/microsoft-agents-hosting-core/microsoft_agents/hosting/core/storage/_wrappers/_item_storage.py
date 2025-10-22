# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Generic, TypeVar

from ..store_item import StoreItem
from ..storage import Storage

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class _ItemStorage(Generic[StoreItemT]):
    """Wrapper around Storage to handle single item operations."""

    def __init__(self, storage: Storage, item_cls: type[StoreItemT]):
        self._storage = storage
        self._item_cls = item_cls

    async def read(self, key: str) -> StoreItemT | None:
        """Reads an item from storage by key.
        
        :param key: The key of the item to read.
        :type key: str
        :return: The item if found, otherwise None.
        """
        res = await self._storage.read([key], target_cls=self._item_cls)
        return res.get(key)
    
    async def write(self, key: str, item: StoreItemT) -> None:
        """Writes an item to storage with the given key.
        
        :param key: The key of the item to write.
        :type key: str
        :param item: The item to write.
        :type item: StoreItemT
        """
        await self._storage.write({key: item})

    async def delete(self, key: str) -> None:
        """Deletes an item from storage by key.
        
        :param key: The key of the item to delete.
        :type key: str
        """
        await self._storage.delete([key])
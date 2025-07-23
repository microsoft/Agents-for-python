from typing import Protocol, TypeVar, Type, Union
from abc import ABC, abstractmethod
from asyncio import gather

from ._type_aliases import JSON
from .store_item import StoreItem, AutoStoreItem, StoreItemDeserializer


StoreItemT = TypeVar("StoreItemT", bound=StoreItem)
AutoStoreItemT = TypeVar("AutoStoreItemT", bound=AutoStoreItem)


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

class ItemStorageBase(Storage):
    """Base class for asynchronous storage implementations with operations
    that work on single items. The bulk operations are implemented in terms
    of the single-item operations.
    """

    async def initialize(self) -> None:
        """Initializes the storage container"""
        pass

    @abstractmethod
    async def read_raw_item(self, key: str) -> tuple[Union[str, None], Union[JSON, None]]:
        """Reads a single item from storage by key.

        Returns a tuple of (key, StoreItem) if found, or (None, None) if not found.
        """
        pass

    async def read_item(self, key: str, target_cls: Type[StoreItemT], **kwargs) -> tuple[Union[str, None], Union[JSON, None]]:
        return await target_cls.from_json_to_store_item(self.read_raw_item(key))

    async def read(
        self, keys: list[str], *, target_cls: Type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")
        if not target_cls:
            raise ValueError("Storage.read(): target_cls cannot be None.")

        await self.initialize()

        raw_items: list[tuple[Union[str, None], Union[JSON, None]]] = await gather(
            *[self._read_item(key, target_cls=target_cls, **kwargs) for key in keys]
        )
        return { key: target_cls.from_json_to_store_item(raw_item) for key, raw_item in raw_items
                if key is not None and raw_item is not None }

    @abstractmethod
    async def write_item(self, key: str, value: StoreItemT) -> None:
        """Writes a single item to storage by key."""
        pass

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        if not changes:
            raise ValueError("Storage.write(): Changes are required when writing.")

        await self.initialize()

        await gather(*[self._write_item(key, value) for key, value in changes.items()])

    @abstractmethod
    async def delete_item(self, key: str) -> None:
        """Deletes a single item from storage by key."""
        pass

    async def delete(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("Storage.delete(): Keys are required when deleting.")

        await self.initialize()

        await gather(*[self._delete_item(key) for key in keys])

class AutoStorageBase(ItemStorageBase):

    async def read_auto(self, keys: list[str], target_cls: list[Type[AutoStoreItemT]]=None, **kwargs) -> dict[str, AutoStoreItemT]:
        if not keys:
            raise ValueError("Storage.read(): Keys are required when reading.")
        if not target_cls and not self._known_types:
            raise ValueError("Storage.read(): target_cls cannot be None.")
        
        target_classes = [*self._known_types]
        if target_cls is None:
            target_classes += [*target_cls]

        await self.initialize()

        raw_items: list[tuple[Union[str, None], Union[JSON, None]]] = await gather(
            *[self.read_raw_item(key) for key in keys]
        )
        items = {}
        deserializer: StoreItemDeserializer = self._auto_deserializer(target_classes)
        for key, raw_item in raw_items.items():
            serialized_item = deserializer(raw_item, deserializer=self._auto_deserializer(target_classes))
            if serialized_item is not None:
                items[key] = serialized_item
        return items
    
    @staticmethod
    def auto_deserializer(target_cls: list[Type[AutoStoreItemT]]) -> StoreItemDeserializer:
        cls_dict = { cls.__name__: cls for cls in target_cls }

        def deserialize(raw_item: JSON) -> AutoStoreItemT:
            cls_name: str = AutoStoreItemT.get_store_item_type(raw_item)
            if not cls_name or cls_name not in cls_dict:
                return None
            return cls_dict[cls_name].from_json_to_store_item(raw_item)
        
        return deserialize
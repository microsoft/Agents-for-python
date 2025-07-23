from abc import ABC
from typing import Protocol, runtime_checkable, Union, Callable, TypeVar, Type

from ._type_aliases import JSON

class StoreItem(ABC):
    def store_item_to_json(self) -> JSON:
        pass

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "StoreItem":
        pass

class AutoStoreItem(StoreItem, Protocol):
    def can_read(raw_item: JSON) -> bool:
        pass

def auto_store_item(item_cls) -> Type[AutoStoreItem]:

    class InnerClass(item_cls.__class__):

        AUTO_TYPE_PROP = "__auto_store_item_type"

        def store_item_to_json(self) -> JSON:
            super().store_item_to_json()
            return {
                AUTO_TYPE_PROP: item_cls.__name__,
                "data": self.wrapped.store_item_to_json()
            }

        @staticmethod
        def from_json_to_store_item(json_data: JSON) -> StoreItem:
            return super().from_json_to_store_item(json_data["data"])
        
        def can_read(raw_item: JSON) -> bool:
            if raw_item is None or AUTO_TYPE_PROP not in raw_item:
                return False
            return raw_item[AUTO_TYPE_PROP] == item_cls.__name__
        
    return InnerClass

StoreItemDeserializer = TypeVar("StoreItemDeserializer", bound=Callable[[Union[JSON, None]], StoreItem])
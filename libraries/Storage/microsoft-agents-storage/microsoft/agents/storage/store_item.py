from typing import Protocol, runtime_checkable

from ._type_aliases import JSON


@runtime_checkable
class StoreItem(Protocol):
    e_tag: str

    def store_item_to_json(self) -> JSON:
        pass

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "StoreItem":
        pass

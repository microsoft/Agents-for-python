from typing import Any, MutableMapping, Protocol
from typing_extensions import Self

JSON = MutableMapping[str, Any]


class StoreItem(Protocol):
    e_tag: str

    def store_item_to_json(self) -> JSON:
        pass

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> Self:
        pass

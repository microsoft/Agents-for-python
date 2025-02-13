from typing import Protocol, TypeVar, Type

from ._type_aliases import JSON
from .store_item import StoreItem


StoreItemT = TypeVar("StoreItemT", bound=StoreItem)


class Storage(Protocol):
    async def read(
        self, keys: list[str], *, target_cls: Type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:
        pass

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        pass

    async def delete(self, keys: list[str]) -> None:
        pass

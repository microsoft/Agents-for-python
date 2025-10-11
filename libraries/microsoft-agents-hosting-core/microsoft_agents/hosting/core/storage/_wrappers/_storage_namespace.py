from typing import TypeVar

from microsoft_agents.activity._error_handling import _raise_if_falsey

from ..storage import Storage
from ..store_item import StoreItem

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class _StorageNamespace(Storage):
    """Wrapper around Storage that manages sign-in state specific to each user and channel.

    Uses the activity's channel_id and from.id to create a key prefix for storage operations.
    """

    def __init__(
        self,
        namespace: str,
        storage: Storage,
    ):
        """
        Args:
            channel_id: used to create the prefix
            user_id: used to create the prefix
            storage: the backing storage
            cache_class: the cache class to use (defaults to DummyCache, which performs no caching).
                This cache's lifetime is tied to the FlowStorageClient instance.
        """

        _raise_if_falsey("StorageNamespace.__init__()", namespace=namespace, storage=storage)

        if not namespace:
            raise ValueError(
                "StorageNamespace.__init__(): namespace must be set."
            )
        
        self._base_key = namespace
        self._storage = storage

    @property
    def base_key(self) -> str:
        """Returns the prefix used for flow state storage isolation."""
        return self._base_key
    
    def key(self, vkey: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self._base_key}:{vkey}"
    
    async def read(
        self, keys: list[str], *, target_cls: type[StoreItemT] = None, **kwargs
    ) -> dict[str, StoreItemT]:
        keys = [self.key(k) for k in keys]
        res = await self._storage.read(keys, target_cls=target_cls, **kwargs)
        virtual_res = {}
        for key in res.keys():
            vkey_start = key.index(":") + 1
            virtual_res[key[vkey_start:]] = res[key]
        return virtual_res

    async def write(self, changes: dict[str, StoreItemT]) -> None:
        changes = {self.key(k): v for k, v in changes.items()}
        await self._storage.write(changes)

    async def delete(self, keys: list[str]) -> None:
        keys = [self.key(k) for k in keys]
        await self._storage.delete(keys)
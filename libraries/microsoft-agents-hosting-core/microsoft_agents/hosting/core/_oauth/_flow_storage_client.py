# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from ..storage import Storage
from ._flow_state import _FlowState


class _DummyCache(Storage):

    async def read(self, keys: list[str], **kwargs) -> dict[str, _FlowState]:
        return {}

    async def write(self, changes: dict[str, _FlowState]) -> None:
        pass

    async def delete(self, keys: list[str]) -> None:
        pass


# this could be generalized. Ideas:
# - CachedStorage class for two-tier storage
# - Namespaced/PrefixedStorage class for namespacing keying
# not generally thread or async safe (operations are not atomic)
class _FlowStorageClient:
    """Wrapper around Storage that manages sign-in state specific to each user and channel.

    Uses the activity's channel_id and from.id to create a key prefix for storage operations.
    """

    def __init__(
        self,
        channel_id: str,
        user_id: str,
        storage: Storage,
        cache_class: Optional[type[Storage]] = None,
    ):
        """
        Args:
            channel_id: used to create the prefix
            user_id: used to create the prefix
            storage: the backing storage
            cache_class: the cache class to use (defaults to DummyCache, which performs no caching).
                This cache's lifetime is tied to the FlowStorageClient instance.
        """

        if not user_id or not channel_id:
            raise ValueError(
                "FlowStorageClient.__init__(): channel_id and user_id must be set."
            )

        self._base_key = f"auth/{channel_id}/{user_id}/"
        self._storage = storage
        if cache_class is None:
            cache_class = _DummyCache
        self._cache = cache_class()

    @property
    def base_key(self) -> str:
        """Returns the prefix used for flow state storage isolation."""
        return self._base_key

    def key(self, auth_handler_id: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self._base_key}{auth_handler_id}"

    async def read(self, auth_handler_id: str) -> Optional[_FlowState]:
        """Reads the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        data = await self._cache.read([key], target_cls=_FlowState)
        if key not in data:
            data = await self._storage.read([key], target_cls=_FlowState)
            if key not in data:
                return None
            await self._cache.write({key: data[key]})
        return _FlowState.model_validate(data.get(key))

    async def write(self, value: _FlowState) -> None:
        """Saves the flow state for a specific authentication handler."""
        key: str = self.key(value.auth_handler_id)
        cached_state = await self._cache.read([key], target_cls=_FlowState)
        if not cached_state or cached_state != value:
            await self._cache.write({key: value})
            await self._storage.write({key: value})

    async def delete(self, auth_handler_id: str) -> None:
        """Deletes the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        cached_state = await self._cache.read([key], target_cls=_FlowState)
        if cached_state:
            await self._cache.delete([key])
        await self._storage.delete([key])

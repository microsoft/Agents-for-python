# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..storage import Storage, StorageProvider
from ..storage.storage_compatibility import (
    as_storage_v2,
    assert_storage_delete_succeeded,
    assert_storage_write_succeeded,
    get_storage_read_value,
)
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
        storage: StorageProvider,
        cache_class: type[StorageProvider] | None = None,
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

    async def read(self, auth_handler_id: str) -> _FlowState | None:
        """Reads the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        cached = await as_storage_v2(self._cache).read([key], target_cls=_FlowState)
        data = get_storage_read_value(cached, key)
        if data is None:
            results = await as_storage_v2(self._storage).read(
                [key], target_cls=_FlowState
            )
            data = get_storage_read_value(results, key)
            if data is None:
                return None
            cached_results = await as_storage_v2(self._cache).write({key: data})
            assert_storage_write_succeeded(cached_results, [key])
        return data

    async def write(self, value: _FlowState) -> None:
        """Saves the flow state for a specific authentication handler."""
        key: str = self.key(value.auth_handler_id)
        cached_results = await as_storage_v2(self._cache).read(
            [key], target_cls=_FlowState
        )
        cached_state = get_storage_read_value(cached_results, key)
        if cached_state != value:
            cache_write = await as_storage_v2(self._cache).write({key: value})
            assert_storage_write_succeeded(cache_write, [key])
            storage_write = await as_storage_v2(self._storage).write({key: value})
            assert_storage_write_succeeded(storage_write, [key])

    async def delete(self, auth_handler_id: str) -> None:
        """Deletes the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        cached_state = await as_storage_v2(self._cache).read(
            [key], target_cls=_FlowState
        )
        if get_storage_read_value(cached_state, key) is not None:
            cache_delete = await as_storage_v2(self._cache).delete([key])
            assert_storage_delete_succeeded(cache_delete, [key])
        storage_delete = await as_storage_v2(self._storage).delete([key])
        assert_storage_delete_succeeded(storage_delete, [key])

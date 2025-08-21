# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from ..storage import Storage, MemoryStorage
from .flow_state import FlowState

class DummyStorage(Storage):

    async def read(self, keys: list[str], **kwargs) -> dict[str, FlowState]:
        return {}

    async def write(self, changes: dict[str, FlowState]) -> None:
        pass

    async def delete(self, keys: list[str]) -> None:
        pass

# this could be generalized, if needed
# not generally thread or async safe
class FlowStorageClient:
    """Wrapper around Storage that manages sign-in state specific to each user and channel.

    Uses the activity's channel_id and from.id to create a key prefix for storage operations.
    """

    def __init__(
        self,
        channel_id: str,
        user_id: str,
        storage: Storage,
        cache_class: type[Storage] = None
    ):
        """
        Parameters
            context: The TurnContext for the current conversation. Used to isolate
                data across channels and users. This defines the prefix used to 
                access storage.
            storage: The Storage instance used to persist flow state data.
        """

        if not user_id or not channel_id:
            raise ValueError("FlowStorageClient.__init__(): channel_id and user_id must be set.")

        self._base_key = f"auth/{channel_id}/{user_id}/"
        self._storage = storage
        if cache_class is None:
            cache_class = DummyStorage
        self._cache = cache_class()

    @property
    def base_key(self) -> str:
        """Returns the prefix used for flow state storage isolation."""
        return self._base_key

    def key(self, auth_handler_id: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self._base_key}{auth_handler_id}"

    async def read(self, auth_handler_id: str) -> Optional[FlowState]:
        """Reads the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        data = await self._cache.read([key], target_cls=FlowState)
        if key not in data:
            data = await self._storage.read([key], target_cls=FlowState)
            if key not in data:
                return None
            await self._cache.write({key: data[key]})
        return FlowState.model_validate(data.get(key))

    async def write(self, value: FlowState) -> None:
        """Saves the flow state for a specific authentication handler."""
        key: str = self.key(value.auth_handler_id)
        cached_state = await self._cache.read([key], target_cls=FlowState)
        if not cached_state or cached_state != value:
            await self._cache.write({key: value})
            await self._storage.write({key: value})

    async def delete(self, auth_handler_id: str) -> None:
        """Deletes the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        cached_state = await self._cache.read([key], target_cls=FlowState)
        if cached_state:
            await self._cache.delete([key])
        await self._storage.delete([key])
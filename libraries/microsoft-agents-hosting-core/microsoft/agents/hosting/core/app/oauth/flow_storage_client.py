from enum import Enum
from typing import Optional

from pydantic import BaseModel

from microsoft.agents.activity import Activity
from microsoft.agents.hosting.core import (
    TurnContext,
    Storage,
    StoreItem
)

# robrandao: TODO -> context.activity.from_property
class FlowStorageClient:
    """
    Wrapper around storage that manages sign-in state specific to each user and channel.

    Uses the activity's channel_id and from.id to create a key prefix for storage operations.
    """

    def __init__(
        self,
        context: TurnContext,
        storage: Storage
    ):

        if (
            not context.activity
            or not context.activity.channel_id
            or not context.activity.from_property
            or not context.activity.from_property.id
        ):

            raise ValueError("context.activity -> channel_id and from.id must be set.")

        channel_id = context.activity.channel_id
        user_id = context.activity.from_property.id

        self.__base_key = f"auth/{channel_id}/{user_id}"
        self.__storage = storage

    def __key(self, id: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self.__base_key}/${id}"

    async def read(self, auth_handler_id: str) -> Optional[FlowState]:
        key: str = self.__key(auth_handler_id)
        data = await self.__storage.read([key], FlowState)
        return data.get(key)  # robrandao: TODO -> verify contract

    async def write(self, value: FlowState) -> None:
        key: str = self.__key(value.id)
        await self.__storage.write({key: value})

    async def delete(self, auth_handler_id: str) -> None:
        key: str = self.__key(auth_handler_id)
        await self.__storage.delete([key])

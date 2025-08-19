from typing import Optional

from microsoft.agents.hosting.core import TurnContext, Storage

from .models import FlowState

# robrandao: TODO -> context.activity.from_property
class FlowStorageClient:
    """
    Wrapper around storage that manages sign-in state specific to each user and channel.

    Uses the activity's channel_id and from.id to create a key prefix for storage operations.

    Contract with other classes (usage of other classes is enforced in unit tests):
        TurnContext.activity.channel_id
        TurnContext.activity.from_property.id

        Storage: read(), write(), delete()
    """

    def __init__(
        self,
        context: TurnContext,
        storage: Storage
    ):
        """
        Parameters
            context: The TurnContext for the current conversation. Used to isolate
                data across channels and users. This defines the prefix used to 
                access storage.
            storage: The Storage instance used to persist flow state data.
        """

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

    @property
    def base_key(self) -> str:
        return self.__base_key

    def key(self, id: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self.__base_key}/${id}"

    async def read(self, auth_handler_id: str) -> Optional[FlowState]:
        """Reads the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        data = await self.__storage.read([key], FlowState)
        return FlowState.validate(data.get(key))  # robrandao: TODO -> verify contract

    async def write(self, value: FlowState) -> None:
        """Saves the flow state for a specific authentication handler."""
        key: str = self.key(value.id)
        await self.__storage.write({key: value})

    async def delete(self, auth_handler_id: str) -> None:
        """Deletes the flow state for a specific authentication handler."""
        key: str = self.key(auth_handler_id)
        await self.__storage.delete([key])

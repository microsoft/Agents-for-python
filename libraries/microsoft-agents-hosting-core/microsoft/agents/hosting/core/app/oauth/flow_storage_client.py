from typing import Optional

from ... import TurnContext
from ...storage import Storage

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
        channel_id: str,
        user_id: str,
        storage: Storage
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

        self.__base_key = f"auth/{channel_id}/{user_id}/"
        self.__storage = storage

    @property
    def base_key(self) -> str:
        return self.__base_key

    @staticmethod
    def key(self, flow_id: str) -> str:
        """Creates a storage key for a specific sign-in handler."""
        return f"{self.__base_key}{flow_id}"

    async def read(self, flow_id: str) -> Optional[FlowState]:
        """Reads the flow state for a specific authentication handler."""
        key: str = self.key(flow_id)
        data = await self.__storage.read([key], FlowState)
        return FlowState.model_validate(data.get(key))  # robrandao: TODO -> verify contract

    async def write(self, value: FlowState) -> None:
        """Saves the flow state for a specific authentication handler."""
        key: str = self.key(value.flow_id)
        await self.__storage.write({key: value})

    async def delete(self, flow_id: str) -> None:
        """Deletes the flow state for a specific authentication handler."""
        key: str = self.key(flow_id)
        await self.__storage.delete([key])

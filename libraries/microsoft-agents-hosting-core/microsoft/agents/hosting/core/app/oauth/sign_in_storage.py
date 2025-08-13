from enum import Enum
from typing import Optional

from pydantic import BaseModel

from microsoft.agents.activity import Activity
from microsoft.agents.hosting.core import StoreItem

class FlowState:
    pass

class SignInHandlerStateStatus(Enum):
    NOT_STARTED = "not_started"
    CONTINUE = "in_progress"
    COMPLETED = "completed"
    FAILURE = "failure"


class SignInHandlerState(BaseModel, StoreItem):
    id: str
    status: SignInHandlerStateStatus
    continuation_activity: Activity

    def store_item_to_json(self): # todo
        return super().store_item_to_json()
    
    @staticmethod
    def from_json_to_store_item(json_data): # todo
        return super().from_json_to_store_item(json_data)


class SignInStorage:

    def __init__(self, context: TurnContext, storage: Storage, handlers: Optional[list[AuthHandler]] = None):

        if (not context.activity or
            not context.activity.channel_id or
            not context.activity.from_property or
            not context.activity.from_property.id):

            raise ValueError("context.activity -> channel_id and from.id must be set.")

        channel_id = context.activity.channel_id
        user_id = context.activity.from_property.id

        self.__base_key = f"auth/{channel_id}/{user_id}"
        self.__handlers = handlers or []
        self.__handler_keys = list(map(create_key, self.__handlers))
        self.__storage = storage

    def create_key(self, id: str) -> str:
        if not self.__base_key:
            raise AttributeError # robrandao: TODO
        return f"{self.__base_key}/${id}"
    
    async def active(self) -> Optional[SignInHandlerState]:
        # batched reads would make this more efficient
        for handler_key in self.__handler_keys:
            state = (await self.__storage.read([handler_key], SignInHandlerState)).get(handler_key)
            if state and state.status == SignInHandlerStateStatus.IN_PROGRESS:
                return state

    async def get(self, id: str) -> Optional[SignInHandlerState]:
        key = self.create_key(id)
        data = await self.__storage.read([key], SignInHandlerState)
        return data.get(key) # robrandao: TODO -> verify contract
    
    async def set(self, value: SignInHandlerState) -> None:
        await self.__storage.write({ self.create_key(value.id): value})

    async def delete(self, id: str) -> None:
        await self.__storage.delete([self.create_key(id)])
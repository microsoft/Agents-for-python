from abc import abstractmethod
from typing import Protocol

class UserTokenBase(Protocol):
    @abstractmethod
    async def get_token(self, user_id: str, connection_name: str, channel_id: str = None, code: str = None) -> dict:
        raise NotImplementedError()

    @abstractmethod
    async def get_aad_tokens(self, user_id: str, connection_name: str, channel_id: str = None, body: dict = None) -> dict:
        raise NotImplementedError()

    @abstractmethod
    async def sign_out(self, user_id: str, connection_name: str = None, channel_id: str = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_token_status(self, user_id: str, channel_id: str = None, include: str = None) -> list:
        raise NotImplementedError()

    @abstractmethod
    async def exchange_token(self, user_id: str, connection_name: str, channel_id: str, body: dict = None) -> dict:
        raise NotImplementedError()

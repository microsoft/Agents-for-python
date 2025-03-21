from abc import abstractmethod
from typing import Protocol

from .agent_sign_in_base import AgentSignInBase
from .user_token_base import UserTokenBase


class UserTokenClientBase(Protocol):
    @property
    @abstractmethod
    def agent_sign_in(self) -> AgentSignInBase:
        pass

    @property
    @abstractmethod
    def user_token(self) -> UserTokenBase:
        pass

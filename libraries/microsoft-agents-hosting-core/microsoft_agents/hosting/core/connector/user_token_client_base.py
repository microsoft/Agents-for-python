# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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


    @abstractmethod
    async def close(self) -> None:
        """Close the client and release any resources."""
        raise NotImplementedError("Subclasses must implement the close method.")
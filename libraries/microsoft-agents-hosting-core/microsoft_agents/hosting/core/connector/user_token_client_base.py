# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol

from .agent_sign_in_base import AgentSignInBase
from .user_token_base import UserTokenBase


class UserTokenClientBase(Protocol):

    @property
    def agent_sign_in(self) -> AgentSignInBase:
        raise NotImplementedError(
            "agent_sign_in property must be implemented by subclasses."
        )

    @property
    @abstractmethod
    def user_token(self) -> UserTokenBase:
        raise NotImplementedError(
            "user_token property must be implemented by subclasses."
        )

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release any resources."""
        raise NotImplementedError("close method must be implemented by subclasses.")

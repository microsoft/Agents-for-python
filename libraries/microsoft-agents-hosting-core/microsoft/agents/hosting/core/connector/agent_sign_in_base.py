from abc import abstractmethod
from typing import Protocol

from microsoft.agents.activity import SignInResource


class AgentSignInBase(Protocol):
    @abstractmethod
    async def get_sign_in_url(
        self,
        state: str,
        code_challenge: str = None,
        emulator_url: str = None,
        final_redirect: str = None,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_sign_in_resource(
        self,
        state: str,
        code_challenge: str = None,
        emulator_url: str = None,
        final_redirect: str = None,
    ) -> SignInResource:
        raise NotImplementedError()

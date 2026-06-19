from abc import abstractmethod
from typing import Protocol

from microsoft_agents.activity import SignInResource


class AgentSignInBase(Protocol):
    @abstractmethod
    async def get_sign_in_url(
        self,
        state: str,
        code_challenge: str | None = None,
        emulator_url: str | None = None,
        final_redirect: str | None = None,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_sign_in_resource(
        self,
        state: str,
        code_challenge: str | None = None,
        emulator_url: str | None = None,
        final_redirect: str | None = None,
    ) -> SignInResource:
        raise NotImplementedError()

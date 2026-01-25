from typing import Callable
from .agent_client import AgentClient

class ConversationClient:

    def __init__(
        self,
        agent_client: AgentClient,
        force_expect_replies: bool = False,
        default_wait: float = 1.0,
        default_timeout: float | None = None,
    ):
        self._client = agent_client
        self._force_expect_replies = force_expect_replies
        self._default_wait = default_wait
        self._default_timeout = default_timeout

    async def say(
        self,
        message: str,
        expect_replies: bool = False,
        wait: bool = False
        timeout: float | None = None
    ) -> None:
        """Send a message without waiting for a response."""
        await self._client.send(message, wait=0.0)

    async def prompt(self, message: str, response_wait: float = 1.0) -> list[Activity]:
        """Send a message and wait for responses."""
        responses = await self._client.send(message, wait=response_wait)
        return responses

    # async def expect(self)

    # async def turn(
    #     self,
    #     message: str,
    #     expect: str | Underscore | Callable | list = None,
    #     response_wait: float | None = None
    # ) -> list[Activity]:
    #     """Send a message, wait for response, optionally assert.

    #     Args:
    #         message: The message to send.
    #         expect: Optional assertion (string, underscore, callable, or list).
    #         response_wait: Time to wait for responses.
    #                     Defaults to 1.0s if expect is set, 0.0s otherwise.
    #     """
    #     if response_wait is None:
    #         response_wait = 1.0 if expect is not None else 0.0

    #     responses = await self._client.send(message, wait=response_wait)

    #     if expect is not None:
    #         self._assert(responses, expect)

    #     return responses
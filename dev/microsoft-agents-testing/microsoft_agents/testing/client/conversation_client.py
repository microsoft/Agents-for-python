from __future__ import annotations

import asyncio
from typing import Callable

from microsoft_agents.activity import Activity

from microsoft_agents.testing.check import Check

from .agent_client import AgentClient
from .exchange import Transcript

class ConversationClient:

    def __init__(
        self,
        agent_client: AgentClient,
        expect_replies: bool = False,
        timeout: float | None = None,
    ):
        self._client = agent_client.child()
        self._transcript = self._client.transcript
        self._expect_replies = expect_replies
        self._timeout = timeout

    @property
    def timeout(self) -> float | None:
        """Get the default timeout value."""
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: float | None) -> None:
        """Set the default timeout value."""
        self._timeout = value

    @property
    def transcript(self) -> Transcript:
        """Get the Transcript associated with this ConversationClient."""
        return self._transcript

    async def say(self, message: str, *, wait: float | None = None) -> list[Activity]:
        """Send a message without waiting for a response."""

        if self._expect_replies:
            return await self._client.send_expect_replies(message, timeout=self._timeout)
        else:
            return await self._client.send(message, wait=wait, timeout=self._timeout)
        
    async def wait_for(self, _filter: str | dict | Callable | None = None, **kwargs) -> list[Activity]:
        """Wait for activities matching criteria.
        
        Uses the ConversationClient.timeout as the wait limit.

        :param _filter: Optional filter criteria (dict or callable).
        :param kwargs: Additional keyword arguments for filtering.
        """

        check = lambda responses: Check(responses).where(_filter, **kwargs).count() > 0

        all_activities = []

        async with asyncio.timeout(self._timeout):
            while True:
                activities = self._client.get_new()
                all_activities.extend(activities)
                if activities and check(activities):
                    break
                await asyncio.sleep(0.1)
        return all_activities
    
    async def expect(self, _filter: dict | Callable | None = None, **kwargs) -> list[Activity]:
        """Wait for activities matching criteria within timeout."""

        try:
            await self.wait_for(_filter, **kwargs)
        except asyncio.TimeoutError:
            raise AssertionError("ConversationClient.expect(): Timeout waiting for expected activities.")
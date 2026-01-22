from __future__ import annotations

import asyncio
from contextlib import contextmanager
from collections.abc import AsyncIterator
from typing import Callable

from microsoft_agents.activity import Activity, InvokeResponse
from microsoft_agents.testing import Check

from .agent_client_config import AgentClientConfig
from .response_collector import ResponseCollector
from .sender_client import SenderClient

class AgentClient(ResponseCollector):
    
    def __init__(self,
                 sender: SenderClient,
                 collector: ResponseCollector,
                 agent_client_config: AgentClientConfig | None = None):
        
        if not sender or not collector:
            raise ValueError("Sender and collector must be provided.")
        
        self._sender: SenderClient = sender
        self._collector: ResponseCollector = collector
        self._filter: Callable[[list[Activity]], Check] | None = None

        self._config = agent_client_config or AgentClientConfig()

    def get_activities(self) -> list[Activity]:
        return self._collector.get_activities()

    def get_invoke_responses(self) -> list[InvokeResponse]:
        return self._collector.get_invoke_responses()
    
    def _fork(self, agent_client_config: AgentClientConfig | None = None) -> AgentClient:
        client = AgentClient(
            self._sender,
            self._collector,
            agent_client_config or self._config
        )
        return client

    async def conversation(self) -> AgentClient:
        pass
    
    async def send(self,
                   activity_or_text: Activity | str,
                   duration: float = 0.0,
                   ) -> list[Activity | InvokeResponse]:

        self._collector.pop()
    
        activities = []
        raw_responses = await self._sender.send(activity_or_text, duration)

        for response in raw_responses:
            self._collector.add(response)
            if not isinstance(response, Activity):
                continue
            activities.append(response)

        if duration != 0.0:
            await asyncio.sleep(duration)

        post_post_activities = self._collector.pop()

        return activities + post_post_activities
    
    async def send_expect_replies(
        self,
        activity_or_Text: Activity | str
    ) -> list[Activity]:
        
    
    def _pop(self) -> list[Activity]:
        new_responses = self._response.pop()
        self._response_history.extend(new_responses)
        return new_responses
    
    async def wait_for_proactive_request(self, timeout: float = 5.0) -> Activity:
        # TODO
        return await self._response.wait_for_proactive_request(timeout)
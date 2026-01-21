from __future__ import annotations

from contextlib import contextmanager

from microsoft_agents.activity import Activity, InvokeResponse
from microsoft_agents.testing import Check

from .response_collector import ResponseCollector
from .response_server import ResponseServer
from .sender_client import SenderClient

class AgentClient:
    
    def __init__(self):
        self._sender_client = SenderClient()
        self._response_server = ResponseServer()

        self._collector = ResponseCollector()
        self._subscribers = [self._collector]
    
    def _clone(self):
        client = AgentClient()
        client._collector = ResponseCollector()
        client._subscribers = []
        self._subscribers.append(client._collector)
        return client

    async def conversation(self) -> AgentClient:
        pass

    @contextmanager
    def listen(self, filter: Check):
        collector = ResponseCollector(filter)
        self._response_collectors.append(collector)
        yield collector
        self._response_collectors.remove(collector)
    
    async def send(self,
                   activity_or_text: Activity | str,
                   duration: float | None = None,
                   return_invoke_responses: bool = False) -> list[Activity | InvokeResponse]:

        self._pop()

        raw_responses = await self._sender.send(activity_or_text, duration)

        responses = []

        for response in raw_responses:
            if isinstance(response, InvokeResponse) and not return_invoke_responses:
                continue
            responses.append(response)

        other_responses = self._pop()

        return responses + other_responses
    
    def _pop(self) -> list[Activity]:
        new_responses = self._response.pop()
        self._response_history.extend(new_responses)
        return new_responses
    
    async def wait_for_proactive_request(self, timeout: float = 5.0) -> Activity:
        # TODO
        return await self._response.wait_for_proactive_request(timeout)
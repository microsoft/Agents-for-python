from typing import Protocol

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import RequestHandler


class A2AHttpAdapter(Protocol):

    @property
    def a2a_request_handler(self) -> RequestHandler:
        ...

    async def execute_agent_turn(self, context: RequestContext, event_queue: EventQueue) -> None:
        ...
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import RequestHandler
from a2a.types import AgentCard

from microsoft_agents.hosting.core import HttpRequestProtocol


class A2AHttpAdapter(Protocol):
    """Protocol for an A2A HTTP adapter."""

    @property
    def a2a_request_handler(self) -> RequestHandler:
        """Get the A2A request handler."""
        ...

    async def execute_agent_turn(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute an agent turn given the request context and event queue.
        
        :param context: The request context for the agent turn.
        :param event_queue: The event queue for the agent turn.
        """
        ...

    async def get_agent_card(self, request: HttpRequestProtocol) -> AgentCard:
        """Process a request for the agent card.

        :param request: The HTTP request for the agent card.
        :return: The agent card for the agent.
        """
        ...
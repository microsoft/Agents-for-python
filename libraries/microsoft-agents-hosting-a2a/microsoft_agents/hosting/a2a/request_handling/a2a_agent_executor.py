# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

from .a2a_http_adapter import A2AHttpAdapter

logger = logging.getLogger(__name__)

class A2AAgentExecutor(AgentExecutor):
    """Executor for handling A2A agent requests."""

    def __init__(self, adapter: A2AHttpAdapter):
        """Initialize the A2A agent executor.

        :param adapter: The A2A adapter instance to use for executing agent turns.
        """
        self._adapter = adapter

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute an A2A agent turn.

        :param context: The request context containing the message and other metadata.
        :param event_queue: The event queue for handling events during the turn.
        """

        if not context.message:
            logger.warning("No message found in the request context. Dropping request.")
            return

        await self._adapter.execute_agent_turn(
            context,
            event_queue,
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel an ongoing A2A agent turn.

        :param context: The request context containing the message and other metadata.
        :param event_queue: The event queue for handling events during the turn.
        """
        pass

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

from microsoft_agents.activity import (
    Activity,
)
from microsoft_agents.hosting.core import (
    Agent,
    ChannelServiceAdapter,
    ClaimsIdentity,
)
from ..activity import A2AActivity, utils
from ..adapter import A2AAdapter

logger = logging.getLogger(__name__)


class A2AAgentExecutor(AgentExecutor):

    def __init__(
        self,
        adapter: A2AAdapter,
    ):
        self._adapter = adapter

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

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
        pass

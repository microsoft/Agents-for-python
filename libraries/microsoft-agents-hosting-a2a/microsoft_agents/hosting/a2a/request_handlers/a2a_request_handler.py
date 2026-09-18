from a2a.types import AgentCard

from a2a.server.tasks import TaskStore
from a2a.server.request_handlers import DefaultRequestHandlerV2

from ..adapter import A2AAdapter

from .a2a_agent_executor import A2AAgentExecutor


class A2ARequestHandler(DefaultRequestHandlerV2):

    def __init__(
        self,
        adapter: A2AAdapter,
        task_store: TaskStore,
        agent_card: AgentCard,
    ):
        self._adapter = adapter
        super().__init__(A2AAgentExecutor(self._adapter), task_store, agent_card)

    def update_agent_card(self, agent_card: AgentCard) -> None:
        """Update the agent card with the provided AgentCard instance.

        :param agent_card: The AgentCard instance to update the handler with.
        """
        self._agent_card = agent_card

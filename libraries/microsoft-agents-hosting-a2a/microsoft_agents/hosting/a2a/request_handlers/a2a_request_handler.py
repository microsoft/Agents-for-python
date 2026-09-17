from a2a.types import AgentCard

from a2a.server.tasks import TaskStore
from a2a.server.request_handlers import RequestHandler, DefaultRequestHandlerV2

from microsoft_agents.hosting.core.channel_adapter_protocol import ChannelAdapterProtocol

from .agent_executor import A2AAgentExecutor

class A2ARequestHandler(DefaultRequestHandlerV2):

    def __init__(
        self,
        adapter: ChannelAdapterProtocol,
        task_store: TaskStore,
        agent_card: AgentCard,
    ):
        self._adapter = adapter
        super().__init__(
            A2AAgentExecutor(self._adapter),
            task_store,
            agent_card
        ) 
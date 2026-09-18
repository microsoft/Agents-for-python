from fastapi import Request, Response

from microsoft_agents.hosting.fastapi import AgentHttpAdapter

from .a2a_adapter import A2AAdapter

from microsoft_agents.hosting.core import (
    Agent,
    Connections,
    ChannelServiceClientFactoryBase,
    OutboundHostValidator,
)
from microsoft_agents.hosting.core.channel_adapter_protocol import (
    ChannelAdapterProtocol,
)

from microsoft_agents.hosting.fastapi import CloudAdapter


class _CloudAdapter(AgentHttpAdapter, ChannelAdapterProtocol):
    pass


class A2ACloudAdapter(A2AAdapter, AgentHttpAdapter):

    def __init__(self):
        pass

    async def process(self, request: Request, agent: Agent) -> Response | None:

        adapted_request = FastApiRequestAdapter(request)

        # Process using base implementation
        http_response: HttpResponse = await self.process_request(adapted_request, agent)

        return await self.process_request(request, agent)

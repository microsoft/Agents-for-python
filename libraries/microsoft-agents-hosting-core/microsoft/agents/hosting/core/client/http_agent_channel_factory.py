from microsoft.agents.hosting.core.authorization import AccessTokenProviderBase

from .channel_factory_protocol import ChannelFactoryProtocol
from .channel_protocol import ChannelProtocol
from .http_agent_channel import HttpAgentChannel


class HttpAgentChannelFactory(ChannelFactoryProtocol):
    def create_channel(self, token_access: AccessTokenProviderBase) -> ChannelProtocol:
        return HttpAgentChannel(token_access)

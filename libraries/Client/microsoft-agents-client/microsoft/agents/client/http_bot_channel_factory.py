from microsoft.agents.authentication import AccessTokenProviderBase

from .channel_factory_protocol import ChannelFactoryProtocol
from .channel_protocol import ChannelProtocol
from .http_bot_channel import HttpBotChannel


class HttpBotChannelFactory(ChannelFactoryProtocol):
    def create_channel(self, token_access: AccessTokenProviderBase) -> ChannelProtocol:
        return HttpBotChannel(token_access)

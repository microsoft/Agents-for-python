from typing import Protocol

from microsoft.agents.authorization import AccessTokenProviderBase

from .channel_protocol import ChannelProtocol


class ChannelFactoryProtocol(Protocol):
    def create_channel(self, token_access: AccessTokenProviderBase) -> ChannelProtocol:
        pass

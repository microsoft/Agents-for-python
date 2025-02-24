from typing import Protocol

from .channel_protocol import ChannelProtocol
from .channel_info_protocol import ChannelInfoProtocol

class ChannelHostProtocol(Protocol):
    def __init__(self, host_endpoint: str, host_app_id: str, channels: dict[str, ChannelInfoProtocol]):
        self.host_endpoint = host_endpoint
        self.host_app_id = host_app_id
        self.channels = channels

    def get_channel(self, channel_info: ChannelInfoProtocol) -> ChannelProtocol:
        raise NotImplementedError()

    def get_channel(self, name: str) -> ChannelProtocol:
        raise NotImplementedError()

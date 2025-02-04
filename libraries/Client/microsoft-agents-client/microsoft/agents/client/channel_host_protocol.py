from typing import Protocol

from .channel_protocol import ChannelProtocol
from .channel_info_protocol import ChannelInfoProtocol


class ChannelHostProtocol(Protocol):
    @property
    def host_endpoint(self) -> str:
        raise NotImplementedError()
    
    @property
    def host_app_id(self) -> str:
        raise NotImplementedError()
    
    @property
    def channels(self) -> dict[str, ChannelInfoProtocol]:
        raise NotImplementedError()
    
    def get_channel(self, channel_info: ChannelInfoProtocol) -> ChannelProtocol:
        raise NotImplementedError()
    
    def get_channel(self, name: str) -> ChannelProtocol:
        raise NotImplementedError()
    

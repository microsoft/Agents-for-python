from typing import Protocol

from .channel_info_protocol import ChannelInfoProtocol


class ChannelInfo(ChannelInfoProtocol):

    def __init__(
        self,
        id: str = None,
        app_id: str = None,
        resource_url: str = None,
        token_provider: str = None,
        channel_factory: str = None,
        endpoint: str = None,
        **kwargs
    ):
        self.id = id
        self.app_id = app_id
        self.resource_url = resource_url
        self.token_provider = token_provider
        self.channel_factory = channel_factory
        self.endpoint = endpoint


class ChannelHostConfiguration(Protocol):

    CHANNELS: list[ChannelInfoProtocol]
    HOST_ENDPOINT: str
    HOST_APP_ID: str


class ChannelsConfiguration(Protocol):

    @staticmethod
    def CHANNEL_HOST_CONFIGURATION() -> ChannelHostConfiguration:
        pass

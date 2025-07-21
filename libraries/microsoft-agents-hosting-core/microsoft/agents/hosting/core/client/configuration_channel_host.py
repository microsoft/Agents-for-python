from copy import copy

from microsoft.agents.hosting.core.authorization import Connections

from .channels_configuration import ChannelsConfiguration
from .channel_factory_protocol import ChannelFactoryProtocol
from .channel_host_protocol import ChannelHostProtocol
from .channel_info_protocol import ChannelInfoProtocol
from .channel_protocol import ChannelProtocol


class ConfigurationChannelHost(ChannelHostProtocol):
    def __init__(
        self,
        channel_factory: ChannelFactoryProtocol,
        connections: Connections,
        configuration: ChannelsConfiguration,
        default_channel_name: str,
    ):
        self._channel_factory = channel_factory
        self.connections = connections
        self.configuration = configuration
        self.channels: dict[str, ChannelInfoProtocol] = {}
        self.host_endpoint: str = None
        self.host_app_id: str = None

        channel_host_configuration = configuration.CHANNEL_HOST_CONFIGURATION()

        if channel_host_configuration:
            if channel_host_configuration.CHANNELS:
                for agent_from_config in channel_host_configuration.CHANNELS:
                    agent = copy(agent_from_config)
                    if not agent.channel_factory:
                        agent.channel_factory = default_channel_name
                    self.channels[agent.id] = agent

            self.host_endpoint = channel_host_configuration.HOST_ENDPOINT
            self.host_app_id = channel_host_configuration.HOST_APP_ID

    def get_channel_from_name(self, name: str) -> ChannelProtocol:
        if not name in self.channels:
            raise ValueError(f"ChannelInfo not found for '{name}'")
        return self.get_channel_from_channel_info(self.channels[name])

    def get_channel_from_channel_info(
        self, channel_info: ChannelInfoProtocol
    ) -> ChannelProtocol:
        if not channel_info:
            raise ValueError(
                f"ConfigurationChannelHost.get_channel_from_channel_info(): channel_info cannot be None"
            )

        token_provider = self.connections.get_connection(channel_info.token_provider)
        if not token_provider:
            raise ValueError(
                f"ConfigurationChannelHost.get_channel_from_channel_info(): token_provider not found for '{channel_info.token_provider}'"
            )

        return self._channel_factory.create_channel(token_provider)

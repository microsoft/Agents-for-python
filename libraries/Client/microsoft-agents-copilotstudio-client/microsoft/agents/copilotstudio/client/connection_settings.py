from typing import Optional
from .direct_to_engine_connection_settings_protocol import (
    DirectToEngineConnectionSettingsProtocol,
)
from .power_platform_cloud import PowerPlatformCloud
from .agent_type import AgentType


class ConnectionSettings(DirectToEngineConnectionSettingsProtocol):
    """
    Connection settings for the DirectToEngineConnectionConfiguration.
    """

    def __init__(
        self,
        environment_id: str,
        agent_identifier: str,
        cloud: Optional[PowerPlatformCloud],
        copilot_agent_type: Optional[AgentType],
        custom_power_platform_cloud: Optional[str],
    ) -> None:
        self.environment_id = environment_id
        self.agent_identifier = agent_identifier

        if not self.environment_id:
            raise ValueError("Environment ID must be provided")
        if not self.agent_identifier:
            raise ValueError("Agent Identifier must be provided")

        self.cloud = cloud or PowerPlatformCloud.UNKNOWN
        self.copilot_agent_type = copilot_agent_type or AgentType.PUBLISHED
        self.custom_power_platform_cloud = custom_power_platform_cloud

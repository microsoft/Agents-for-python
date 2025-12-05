# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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
        cloud: Optional[PowerPlatformCloud] = None,
        copilot_agent_type: Optional[AgentType] = None,
        custom_power_platform_cloud: Optional[str] = None,
        client_session_settings: Optional[dict] = None,
    ) -> None:
        """Initialize connection settings.

        :param environment_id: The ID of the environment to connect to.
        :param agent_identifier: The identifier of the agent to use for the connection.
        :param cloud: The PowerPlatformCloud to use for the connection.
        :param copilot_agent_type: The AgentType to use for the Copilot.
        :param custom_power_platform_cloud: The custom PowerPlatformCloud URL.
        :param client_session_settings: Additional arguments for initialization
            of the underlying Aiohttp ClientSession.
        """

        self.environment_id = environment_id
        self.agent_identifier = agent_identifier

        if not self.environment_id:
            raise ValueError("Environment ID must be provided")
        if not self.agent_identifier:
            raise ValueError("Agent Identifier must be provided")

        self.cloud = cloud or PowerPlatformCloud.PROD
        self.copilot_agent_type = copilot_agent_type or AgentType.PUBLISHED
        self.custom_power_platform_cloud = custom_power_platform_cloud
        self.client_session_settings = client_session_settings or {}

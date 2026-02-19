# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ
from typing import Dict, Optional, Any
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
        direct_connect_url: Optional[str] = None,
        use_experimental_endpoint: bool = False,
        enable_diagnostics: bool = False,
    ) -> None:
        """Initialize connection settings.

        :param environment_id: The ID of the environment to connect to.
        :param agent_identifier: The identifier of the agent to use for the connection.
        :param cloud: The PowerPlatformCloud to use for the connection.
        :param copilot_agent_type: The AgentType to use for the Copilot.
        :param custom_power_platform_cloud: The custom PowerPlatformCloud URL.
        :param client_session_settings: Additional arguments for initialization
            of the underlying Aiohttp ClientSession.
        :param direct_connect_url: Direct connection URL override.
        :param use_experimental_endpoint: Flag to enable experimental endpoint.
        :param enable_diagnostics: Flag to enable diagnostics.
        """

        self.environment_id = environment_id
        self.agent_identifier = agent_identifier

        if not self.environment_id and not direct_connect_url:
            raise ValueError("Environment ID or Direct Connect URL must be provided")
        if not self.agent_identifier and not direct_connect_url:
            raise ValueError("Agent Identifier or Direct Connect URL must be provided")

        self.cloud = cloud or PowerPlatformCloud.PROD
        self.copilot_agent_type = copilot_agent_type or AgentType.PUBLISHED
        self.custom_power_platform_cloud = custom_power_platform_cloud
        self.client_session_settings = client_session_settings or {}
        self.direct_connect_url = direct_connect_url
        self.use_experimental_endpoint = use_experimental_endpoint
        self.enable_diagnostics = enable_diagnostics

    @staticmethod
    def populate_from_environment(
        environment_id: Optional[str] = None,
        agent_identifier: Optional[str] = None,
        cloud: Optional[PowerPlatformCloud] = None,
        copilot_agent_type: Optional[AgentType] = None,
        custom_power_platform_cloud: Optional[str] = None,
        direct_connect_url: Optional[str] = None,
        use_experimental_endpoint: Optional[bool] = None,
        enable_diagnostics: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Populate connection settings from environment variables.

        This method reads configuration values from environment variables
        and returns them as a dictionary suitable for passing to ConnectionSettings.__init__().

        :param environment_id: Optional override for ENVIRONMENT_ID env var.
        :param agent_identifier: Optional override for AGENT_IDENTIFIER env var.
        :param cloud: Optional override for CLOUD env var.
        :param copilot_agent_type: Optional override for COPILOT_AGENT_TYPE env var.
        :param custom_power_platform_cloud: Optional override for CUSTOM_POWER_PLATFORM_CLOUD env var.
        :param direct_connect_url: Optional override for DIRECT_CONNECT_URL env var.
        :param use_experimental_endpoint: Optional override for USE_EXPERIMENTAL_ENDPOINT env var.
        :param enable_diagnostics: Optional override for ENABLE_DIAGNOSTICS env var.
        :return: Dictionary of connection settings.
        """
        # Read from environment variables with provided overrides
        env_id = environment_id or environ.get("ENVIRONMENT_ID", "")
        agent_id = agent_identifier or environ.get("AGENT_IDENTIFIER", "")

        # Handle cloud enum
        cloud_value = cloud
        if cloud_value is None:
            cloud_str = environ.get("CLOUD", "PROD")
            try:
                cloud_value = PowerPlatformCloud[cloud_str]
            except KeyError:
                cloud_value = PowerPlatformCloud.PROD

        # Handle copilot agent type enum
        agent_type_value = copilot_agent_type
        if agent_type_value is None:
            agent_type_str = environ.get("COPILOT_AGENT_TYPE", "PUBLISHED")
            try:
                agent_type_value = AgentType[agent_type_str]
            except KeyError:
                agent_type_value = AgentType.PUBLISHED

        # Handle other settings
        custom_cloud = custom_power_platform_cloud or environ.get(
            "CUSTOM_POWER_PLATFORM_CLOUD", None
        )
        direct_url = direct_connect_url or environ.get("DIRECT_CONNECT_URL", None)

        # Handle boolean flags
        exp_endpoint = use_experimental_endpoint
        if exp_endpoint is None:
            exp_endpoint = (
                environ.get("USE_EXPERIMENTAL_ENDPOINT", "false").lower() == "true"
            )

        diagnostics = enable_diagnostics
        if diagnostics is None:
            diagnostics = environ.get("ENABLE_DIAGNOSTICS", "false").lower() == "true"

        return {
            "environment_id": env_id,
            "agent_identifier": agent_id,
            "cloud": cloud_value,
            "copilot_agent_type": agent_type_value,
            "custom_power_platform_cloud": custom_cloud,
            "direct_connect_url": direct_url,
            "use_experimental_endpoint": exp_endpoint,
            "enable_diagnostics": diagnostics,
        }

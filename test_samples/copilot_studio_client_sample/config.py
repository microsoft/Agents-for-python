from os import environ
from typing import Optional

from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    PowerPlatformCloud,
    AgentType,
)


class McsConnectionSettings(ConnectionSettings):
    def __init__(
        self,
        app_client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        agent_identifier: Optional[str] = None,
        cloud: Optional[PowerPlatformCloud] = None,
        copilot_agent_type: Optional[AgentType] = None,
        custom_power_platform_cloud: Optional[str] = None,
        direct_connect_url: Optional[str] = None,
        use_experimental_endpoint: Optional[bool] = None,
        enable_diagnostics: Optional[bool] = None,
    ) -> None:
        self.app_client_id = app_client_id or environ.get("APP_CLIENT_ID")
        self.tenant_id = tenant_id or environ.get("TENANT_ID")

        if not self.app_client_id:
            raise ValueError("App Client ID must be provided")
        if not self.tenant_id:
            raise ValueError("Tenant ID must be provided")

        # Use the parent class's method to populate settings from environment
        settings = ConnectionSettings.populate_from_environment(
            environment_id=environment_id,
            agent_identifier=agent_identifier,
            cloud=cloud,
            copilot_agent_type=copilot_agent_type,
            custom_power_platform_cloud=custom_power_platform_cloud,
            direct_connect_url=direct_connect_url,
            use_experimental_endpoint=use_experimental_endpoint,
            enable_diagnostics=enable_diagnostics,
        )

        # Initialize the parent class with the populated settings
        super().__init__(**settings)

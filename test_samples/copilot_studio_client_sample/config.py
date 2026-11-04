from microsoft_agents.activity.config import Configuration
from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    PowerPlatformCloud,
    AgentType,
)


class McsConnectionSettings(ConnectionSettings):
    def __init__(self, config: Configuration) -> None:
        self.app_client_id = config.get_str("APP_CLIENT_ID", default=None)
        self.tenant_id = config.get_str("TENANT_ID", default=None)

        if not self.app_client_id:
            raise ValueError("App Client ID must be provided")
        if not self.tenant_id:
            raise ValueError("Tenant ID must be provided")

        super().__init__(
            environment_id=config.get_str("ENVIRONMENT_ID", default=""),
            agent_identifier=config.get_str("AGENT_IDENTIFIER", default=""),
            cloud=PowerPlatformCloud[config.get_str("CLOUD", default="PROD")],
            copilot_agent_type=AgentType[
                config.get_str("COPILOT_AGENT_TYPE", default="PUBLISHED")
            ],
            custom_power_platform_cloud=config.get_str(
                "CUSTOM_POWER_PLATFORM_CLOUD", default=None
            ),
            direct_connect_url=config.get_str("DIRECT_CONNECT_URL", default=None),
            use_experimental_endpoint=config.get_bool(
                "USE_EXPERIMENTAL_ENDPOINT", default=False
            ),
            enable_diagnostics=config.get_bool("ENABLE_DIAGNOSTICS", default=False),
        )

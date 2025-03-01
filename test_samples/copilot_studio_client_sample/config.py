from os import environ
from typing import Optional

from microsoft.agents.copilotstudio.client import (
    ConnectionSettings,
    PowerPlatformCloud,
    BotType,
)


class McsConnectionSettings(ConnectionSettings):
    def __init__(
        self,
        app_client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        bot_identifier: Optional[str] = None,
        cloud: Optional[PowerPlatformCloud] = None,
        copilot_bot_type: Optional[BotType] = None,
        custom_power_platform_cloud: Optional[str] = None,
    ) -> None:
        self.app_client_id = app_client_id or environ.get("APP_CLIENT_ID")
        self.tenant_id = tenant_id or environ.get("TENANT_ID")

        if not self.app_client_id:
            raise ValueError("App Client ID must be provided")
        if not self.tenant_id:
            raise ValueError("Tenant ID must be provided")

        environment_id = environment_id or environ.get("ENVIRONMENT_ID")
        bot_identifier = bot_identifier or environ.get("BOT_IDENTIFIER")
        cloud = cloud or PowerPlatformCloud[environ.get("CLOUD", "UNKNOWN")]
        copilot_bot_type = (
            copilot_bot_type or BotType[environ.get("COPILOT_BOT_TYPE", "PUBLISHED")]
        )
        custom_power_platform_cloud = custom_power_platform_cloud or environ.get(
            "CUSTOM_POWER_PLATFORM_CLOUD", None
        )

        super().__init__(
            environment_id,
            bot_identifier,
            cloud,
            copilot_bot_type,
            custom_power_platform_cloud,
        )

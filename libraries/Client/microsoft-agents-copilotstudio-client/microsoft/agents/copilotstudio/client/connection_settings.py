from typing import Optional
from .direct_to_engine_connection_settings_protocol import (
    DirectToEngineConnectionSettingsProtocol,
)
from .power_platform_cloud import PowerPlatformCloud
from .bot_type import BotType


class ConnectionSettings(DirectToEngineConnectionSettingsProtocol):
    """
    Connection settings for the DirectToEngineConnectionConfiguration.
    """

    def __init__(
        self,
        environment_id: str,
        bot_identifier: str,
        cloud: Optional[PowerPlatformCloud],
        copilot_bot_type: Optional[BotType],
        custom_power_platform_cloud: Optional[str],
    ) -> None:
        self.environment_id = environment_id
        self.bot_identifier = bot_identifier

        if not self.environment_id:
            raise ValueError("Environment ID must be provided")
        if not self.bot_identifier:
            raise ValueError("Bot Identifier must be provided")

        self.cloud = cloud or PowerPlatformCloud.UNKNOWN
        self.copilot_bot_type = copilot_bot_type or BotType.PUBLISHED
        self.custom_power_platform_cloud = custom_power_platform_cloud

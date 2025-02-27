from .direct_to_engine_connection_settings_protocol import (
    DirectToEngineConnectionSettingsProtocol,
)
from .power_platform_cloud import PowerPlatformCloud
from .bot_type import BotType


# TODO: Should rename to MCSConnectionSettings?
class ConnectionSettings(DirectToEngineConnectionSettingsProtocol):
    """
    Connection settings for the DirectToEngineConnectionConfiguration.
    """

    def __init__(self, config: dict):
        if config:
            self.ENVIRONMENT_ID = config["ENVIRONMENT_ID"]
            self.BOT_IDENTIFIER = config["BOT_IDENTIFIER"]
            self.CLOUD = config.get("CLOUD", PowerPlatformCloud.UNKNOWN)
            self.COPILOT_BOT_TYPE = config.get("COPILOT_BOT_TYPE", BotType.PUBLISHED)
            self.CUSTOM_POWER_PLATFORM_CLOUD = config.get("CUSTOM_POWER_PLATFORM_CLOUD")

from typing import Protocol, Optional

from .bot_type import BotType
from .power_platform_cloud import PowerPlatformCloud


class DirectToEngineConnectionSettingsProtocol(Protocol):
    """
    Protocol for DirectToEngineConnectionConfiguration.
    """

    # Schema name for the Copilot Studio Hosted Copilot.
    bot_identifier: Optional[str]

    # if PowerPlatformCloud is set to Other, this is the url for the power platform API endpoint.
    custom_power_platform_cloud: Optional[str]

    # Environment ID for the environment that hosts the bot
    environment_id: Optional[str]

    # Power Platform Cloud where the environment is hosted
    cloud: Optional[PowerPlatformCloud]

    # Type of Bot hosted in Copilot Studio
    copilot_bot_type: Optional[BotType]

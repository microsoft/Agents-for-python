from typing import Protocol, Optional

from .bot_type import BotType
from .power_platform_cloud import PowerPlatformCloud


class DirectToEngineConnectionConfigurationProtocol(Protocol):
    """
    Protocol for DirectToEngineConnectionConfiguration.
    """

    # Schema name for the Copilot Studio Hosted Copilot.

    BOT_IDENTIFIER: Optional[str]

    # if PowerPlatformCloud is set to Other, this is the url for the power platform API endpoint.

    CUSTOM_POWER_PLATFORM_CLOUD: Optional[str]

    # Environment ID for the environment that hosts the bot

    EnvironmentId: Optional[str]

    # Power Platform Cloud where the environment is hosted

    CLOUD: Optional[PowerPlatformCloud]

    # Type of Bot hosted in Copilot Studio

    COPILOT_BOT_TYPE: Optional[BotType]

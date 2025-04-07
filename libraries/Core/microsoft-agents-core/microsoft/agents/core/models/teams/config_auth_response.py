# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field

from .config_response import ConfigResponse
from .bot_config_auth import BotConfigAuth


class ConfigAuthResponse(ConfigResponse):
    """Response for configuration authentication.

    :param suggested_actions: Suggested actions for the configuration authentication.
    :type suggested_actions: object
    """

    config: BotConfigAuth = Field(default_factory=lambda: BotConfigAuth())

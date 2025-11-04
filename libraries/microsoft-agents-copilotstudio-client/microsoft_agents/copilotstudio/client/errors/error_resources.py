# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Copilot Studio error resources for Microsoft Agents SDK.

Error codes are in the range -65000 to -65999.
"""

from .error_message import ErrorMessage


class CopilotStudioErrorResources:
    """
    Error messages for Copilot Studio operations.

    Error codes are organized in the range -65000 to -65999.
    """

    CloudBaseAddressRequired = ErrorMessage(
        "cloud_base_address must be provided when PowerPlatformCloud is Other",
        -65000,
        "copilot-studio-client",
    )

    EnvironmentIdRequired = ErrorMessage(
        "EnvironmentId must be provided",
        -65001,
        "copilot-studio-client",
    )

    AgentIdentifierRequired = ErrorMessage(
        "AgentIdentifier must be provided",
        -65002,
        "copilot-studio-client",
    )

    CustomCloudOrBaseAddressRequired = ErrorMessage(
        "Either CustomPowerPlatformCloud or cloud_base_address must be provided when PowerPlatformCloud is Other",
        -65003,
        "copilot-studio-client",
    )

    InvalidConnectionSettingsType = ErrorMessage(
        "connection_settings must be of type DirectToEngineConnectionSettings",
        -65004,
        "copilot-studio-client",
    )

    PowerPlatformEnvironmentRequired = ErrorMessage(
        "PowerPlatformEnvironment must be provided",
        -65005,
        "copilot-studio-client",
    )

    AccessTokenProviderRequired = ErrorMessage(
        "AccessTokenProvider must be provided",
        -65006,
        "copilot-studio-client",
    )

    def __init__(self):
        """Initialize CopilotStudioErrorResources."""
        pass

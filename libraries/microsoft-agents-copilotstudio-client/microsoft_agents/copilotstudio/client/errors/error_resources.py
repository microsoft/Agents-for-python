# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Copilot Studio error resources for Microsoft Agents SDK.

Error codes are in the range -65000 to -65999.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage


class CopilotStudioErrorResources:
    """
    Error messages for Copilot Studio operations.

    Error codes are organized in the range -65000 to -65999.
    """

    CloudBaseAddressRequired = ErrorMessage(
        "cloud_base_address must be provided when PowerPlatformCloud is Other",
        -65000,
    )

    EnvironmentIdRequired = ErrorMessage(
        "EnvironmentId must be provided",
        -65001,
    )

    AgentIdentifierRequired = ErrorMessage(
        "AgentIdentifier must be provided",
        -65002,
    )

    CustomCloudOrBaseAddressRequired = ErrorMessage(
        "Either CustomPowerPlatformCloud or cloud_base_address must be provided when PowerPlatformCloud is Other",
        -65003,
    )

    InvalidConnectionSettingsType = ErrorMessage(
        "connection_settings must be of type DirectToEngineConnectionSettings",
        -65004,
    )

    PowerPlatformEnvironmentRequired = ErrorMessage(
        "PowerPlatformEnvironment must be provided",
        -65005,
    )

    AccessTokenProviderRequired = ErrorMessage(
        "AccessTokenProvider must be provided",
        -65006,
    )

    def __init__(self):
        """Initialize CopilotStudioErrorResources."""
        pass

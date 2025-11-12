# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Authentication error resources for Microsoft Agents SDK.

Error codes are in the range -60000 to -60999.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage


class AuthenticationErrorResources:
    """
    Error messages for authentication operations.

    Error codes are organized in the range -60000 to -60999.
    """

    FailedToAcquireToken = ErrorMessage(
        "Failed to acquire token. {0}",
        -60012,
    )

    InvalidInstanceUrl = ErrorMessage(
        "Invalid instance URL",
        -60013,
    )

    OnBehalfOfFlowNotSupportedManagedIdentity = ErrorMessage(
        "On-behalf-of flow is not supported with Managed Identity authentication.",
        -60014,
    )

    OnBehalfOfFlowNotSupportedAuthType = ErrorMessage(
        "On-behalf-of flow is not supported with the current authentication type: {0}",
        -60015,
    )

    AuthenticationTypeNotSupported = ErrorMessage(
        "Authentication type not supported",
        -60016,
    )

    AgentApplicationInstanceIdRequired = ErrorMessage(
        "Agent application instance Id must be provided.",
        -60017,
    )

    FailedToAcquireAgenticInstanceToken = ErrorMessage(
        "Failed to acquire agentic instance token or agent token for agent_app_instance_id {0}",
        -60018,
    )

    AgentApplicationInstanceIdAndUserIdRequired = ErrorMessage(
        "Agent application instance Id and agentic user Id must be provided.",
        -60019,
    )

    FailedToAcquireInstanceOrAgentToken = ErrorMessage(
        "Failed to acquire instance token or agent token for agent_app_instance_id {0} and agentic_user_id {1}",
        -60020,
    )

    def __init__(self):
        """Initialize AuthenticationErrorResources."""
        pass

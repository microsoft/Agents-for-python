# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for the Microsoft Agents Entra ID Auth Sidecar package.

Error codes are in the range -61000 to -61999.
"""

from microsoft_agents.activity.errors import ErrorMessage


class SidecarAuthError(Exception):
    """Base exception for sidecar authentication errors."""


class SidecarUnavailableError(SidecarAuthError):
    """Raised when the sidecar is unreachable (connection refused, timeout, exhausted retries)."""


class SidecarConfigurationError(SidecarAuthError):
    """Raised when the sidecar returns 404 (misconfigured downstream API / resource name)."""


class SidecarAuthErrorResources:
    """
    Error messages for sidecar authentication operations.

    Error codes are organized in the range -61000 to -61999.
    """

    InvalidBaseUrl = ErrorMessage(
        "The resolved sidecar base URL '{0}' is not a valid absolute http(s) URL.",
        -61000,
    )

    BaseUrlMustNotContainUserInfo = ErrorMessage(
        "The resolved sidecar base URL '{0}' must not contain userinfo (credentials).",
        -61001,
    )

    BaseUrlNotLoopbackOrPrivate = ErrorMessage(
        "The resolved sidecar base URL '{0}' points to a non-loopback, non-private address. "
        "The Entra ID Agent Container must be reachable only from within the agent's network "
        "boundary. Set 'BYPASS_LOCAL_NETWORK_RESTRICTION' to true in the connection "
        "configuration to override this safety check (UNSAFE: only for carefully validated "
        "private-network configurations).",
        -61002,
    )

    AgentUserIdAndUsernameMutuallyExclusive = ErrorMessage(
        "AgentUsername and AgentUserId are mutually exclusive; set only one.",
        -61003,
    )

    SidecarRequestFailed = ErrorMessage(
        "Sidecar request failed after {0} attempt(s): {1}",
        -61004,
    )

    SidecarReturnedError = ErrorMessage(
        "Sidecar returned {0}: {1}",
        -61005,
    )

    SidecarResponseMissingHeader = ErrorMessage(
        "Sidecar response missing 'authorizationHeader' field.",
        -61006,
    )

    SidecarResponseUnparsable = ErrorMessage(
        "Sidecar returned an unparsable response body.",
        -61007,
    )

    AgentApplicationInstanceIdRequired = ErrorMessage(
        "Agent application instance Id must be provided.",
        -61008,
    )

    AgentApplicationInstanceIdAndUserIdRequired = ErrorMessage(
        "Agent application instance Id and agentic user Id must be provided.",
        -61009,
    )

    def __init__(self):
        """Initialize SidecarAuthErrorResources."""
        pass

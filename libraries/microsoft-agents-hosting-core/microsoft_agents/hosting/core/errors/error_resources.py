# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Hosting core error resources for Microsoft Agents SDK.

This module contains error messages for hosting operations.
Error codes are in the range -63000 to -63999 for hosting errors.
General/validation errors are in the range -66000 to -66999.
"""

from .error_message import ErrorMessage


class ErrorResources:
    """
    Error messages for hosting core operations.

    Error codes are organized by range:
    - -63000 to -63999: Hosting errors
    - -66000 to -66999: General/validation errors
    """

    # Hosting Errors (-63000 to -63999)
    AdapterRequired = ErrorMessage(
        "start_agent_process: adapter can't be None",
        -63000,
    )

    AgentApplicationRequired = ErrorMessage(
        "start_agent_process: agent_application can't be None",
        -63001,
    )

    RequestRequired = ErrorMessage(
        "CloudAdapter.process: request can't be None",
        -63002,
    )

    AgentRequired = ErrorMessage(
        "CloudAdapter.process: agent can't be None",
        -63003,
    )

    StreamAlreadyEnded = ErrorMessage(
        "The stream has already ended.",
        -63004,
    )

    TurnContextRequired = ErrorMessage(
        "TurnContext cannot be None.",
        -63005,
    )

    ActivityRequired = ErrorMessage(
        "Activity cannot be None.",
        -63006,
    )

    AppIdRequired = ErrorMessage(
        "AppId cannot be empty or None.",
        -63007,
    )

    InvalidActivityType = ErrorMessage(
        "Invalid or missing activity type.",
        -63008,
    )

    ConversationIdRequired = ErrorMessage(
        "Conversation ID cannot be empty or None.",
        -63009,
    )

    AuthHeaderRequired = ErrorMessage(
        "Authorization header is required.",
        -63010,
    )

    InvalidAuthHeader = ErrorMessage(
        "Invalid authorization header format.",
        -63011,
    )

    ClaimsIdentityRequired = ErrorMessage(
        "ClaimsIdentity is required.",
        -63012,
    )

    ChannelServiceRouteNotFound = ErrorMessage(
        "Channel service route not found for: {0}",
        -63013,
    )

    TokenExchangeRequired = ErrorMessage(
        "Token exchange requires a token exchange resource.",
        -63014,
    )

    MissingHttpClient = ErrorMessage(
        "HTTP client is required.",
        -63015,
    )

    InvalidBotFrameworkActivity = ErrorMessage(
        "Invalid Bot Framework Activity format.",
        -63016,
    )

    CredentialsRequired = ErrorMessage(
        "Credentials are required for authentication.",
        -63017,
    )

    # General/Validation Errors (-66000 to -66999)
    InvalidConfiguration = ErrorMessage(
        "Invalid configuration: {0}",
        -66000,
    )

    RequiredParameterMissing = ErrorMessage(
        "Required parameter missing: {0}",
        -66001,
    )

    InvalidParameterValue = ErrorMessage(
        "Invalid parameter value for {0}: {1}",
        -66002,
    )

    OperationNotSupported = ErrorMessage(
        "Operation not supported: {0}",
        -66003,
    )

    ResourceNotFound = ErrorMessage(
        "Resource not found: {0}",
        -66004,
    )

    UnexpectedError = ErrorMessage(
        "An unexpected error occurred: {0}",
        -66005,
    )

    InvalidStateObject = ErrorMessage(
        "Invalid state object: {0}",
        -66006,
    )

    SerializationError = ErrorMessage(
        "Serialization error: {0}",
        -66007,
    )

    DeserializationError = ErrorMessage(
        "Deserialization error: {0}",
        -66008,
    )

    TimeoutError = ErrorMessage(
        "Operation timed out: {0}",
        -66009,
    )

    NetworkError = ErrorMessage(
        "Network error occurred: {0}",
        -66010,
    )

    def __init__(self):
        """Initialize ErrorResources singleton."""
        pass

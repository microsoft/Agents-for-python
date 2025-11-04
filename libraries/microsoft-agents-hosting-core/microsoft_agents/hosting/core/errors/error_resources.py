# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Central error resource file for Microsoft Agents SDK.

This module contains all error messages used throughout the SDK, each with:
- A formatting string
- An error code (aligned with C# SDK pattern)
- A help URL anchor

Error codes are negative integers following the Microsoft Agents SDK convention.
"""

from .error_message import ErrorMessage


class ErrorResources:
    """
    Central repository of all error messages used in the Microsoft Agents SDK.

    Error codes are organized by range:
    - -60000 to -60099: Authentication errors
    - -60100 to -60199: Storage errors
    - -60200 to -60299: Teams-specific errors
    - -60300 to -60399: Hosting errors
    - -60400 to -60499: Activity errors
    - -60500 to -60599: Copilot Studio errors
    - -60600 to -60699: General/validation errors
    """

    # Authentication Errors (-60000 to -60099)
    FailedToAcquireToken = ErrorMessage(
        "Failed to acquire token. {0}",
        -60012,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    InvalidInstanceUrl = ErrorMessage(
        "Invalid instance URL",
        -60013,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    OnBehalfOfFlowNotSupportedManagedIdentity = ErrorMessage(
        "On-behalf-of flow is not supported with Managed Identity authentication.",
        -60014,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    OnBehalfOfFlowNotSupportedAuthType = ErrorMessage(
        "On-behalf-of flow is not supported with the current authentication type: {0}",
        -60015,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    AuthenticationTypeNotSupported = ErrorMessage(
        "Authentication type not supported",
        -60016,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    AgentApplicationInstanceIdRequired = ErrorMessage(
        "Agent application instance Id must be provided.",
        -60017,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    FailedToAcquireAgenticInstanceToken = ErrorMessage(
        "Failed to acquire agentic instance token or agent token for agent_app_instance_id {0}",
        -60018,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    AgentApplicationInstanceIdAndUserIdRequired = ErrorMessage(
        "Agent application instance Id and agentic user Id must be provided.",
        -60019,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    FailedToAcquireInstanceOrAgentToken = ErrorMessage(
        "Failed to acquire instance token or agent token for agent_app_instance_id {0} and agentic_user_id {1}",
        -60020,
        "agentic-identity-with-the-m365-agents-sdk",
    )

    # Storage Errors (-60100 to -60199)
    CosmosDbConfigRequired = ErrorMessage(
        "CosmosDBStorage: CosmosDBConfig is required.",
        -60100,
        "storage-configuration",
    )

    CosmosDbEndpointRequired = ErrorMessage(
        "CosmosDBStorage: cosmos_db_endpoint is required.",
        -60101,
        "storage-configuration",
    )

    CosmosDbAuthKeyRequired = ErrorMessage(
        "CosmosDBStorage: auth_key is required.",
        -60102,
        "storage-configuration",
    )

    CosmosDbDatabaseIdRequired = ErrorMessage(
        "CosmosDBStorage: database_id is required.",
        -60103,
        "storage-configuration",
    )

    CosmosDbContainerIdRequired = ErrorMessage(
        "CosmosDBStorage: container_id is required.",
        -60104,
        "storage-configuration",
    )

    CosmosDbKeyCannotBeEmpty = ErrorMessage(
        "CosmosDBStorage: Key cannot be empty.",
        -60105,
        "storage-configuration",
    )

    CosmosDbPartitionKeyInvalid = ErrorMessage(
        "CosmosDBStorage: PartitionKey of {0} cannot be used with a CosmosDbPartitionedStorageOptions.PartitionKey of {1}.",
        -60106,
        "storage-configuration",
    )

    CosmosDbPartitionKeyPathInvalid = ErrorMessage(
        "CosmosDBStorage: PartitionKeyPath must match cosmosDbPartitionedStorageOptions value of {0}",
        -60107,
        "storage-configuration",
    )

    CosmosDbCompatibilityModeRequired = ErrorMessage(
        "CosmosDBStorage: compatibilityMode cannot be set when using partitionKey options.",
        -60108,
        "storage-configuration",
    )

    CosmosDbPartitionKeyNotFound = ErrorMessage(
        "CosmosDBStorage: Partition key '{0}' missing from state, you may be missing custom state implementation.",
        -60109,
        "storage-configuration",
    )

    CosmosDbInvalidPartitionKeyValue = ErrorMessage(
        "CosmosDBStorage: Invalid PartitionKey property on item with id {0}",
        -60110,
        "storage-configuration",
    )

    BlobStorageConfigRequired = ErrorMessage(
        "BlobStorage: BlobStorageConfig is required.",
        -60120,
        "storage-configuration",
    )

    BlobConnectionStringOrUrlRequired = ErrorMessage(
        "BlobStorage: either connection_string or container_url is required.",
        -60121,
        "storage-configuration",
    )

    BlobContainerNameRequired = ErrorMessage(
        "BlobStorage: container_name is required.",
        -60122,
        "storage-configuration",
    )

    StorageKeyCannotBeEmpty = ErrorMessage(
        "Storage: Key cannot be empty.",
        -60130,
        "storage-configuration",
    )

    StorageInvalidJsonBlob = ErrorMessage(
        "Storage: Blob {0} could not be decoded as JSON. {1}",
        -60131,
        "storage-configuration",
    )

    # Teams Errors (-60200 to -60299)
    TeamsBadRequest = ErrorMessage(
        "BadRequest",
        -60200,
        "teams-integration",
    )

    TeamsNotImplemented = ErrorMessage(
        "NotImplemented",
        -60201,
        "teams-integration",
    )

    TeamsContextRequired = ErrorMessage(
        "context is required.",
        -60202,
        "teams-integration",
    )

    TeamsMeetingIdRequired = ErrorMessage(
        "meeting_id is required.",
        -60203,
        "teams-integration",
    )

    TeamsParticipantIdRequired = ErrorMessage(
        "participant_id is required.",
        -60204,
        "teams-integration",
    )

    TeamsTeamIdRequired = ErrorMessage(
        "team_id is required.",
        -60205,
        "teams-integration",
    )

    TeamsTurnContextRequired = ErrorMessage(
        "TurnContext cannot be None",
        -60206,
        "teams-integration",
    )

    TeamsActivityRequired = ErrorMessage(
        "Activity cannot be None",
        -60207,
        "teams-integration",
    )

    TeamsChannelIdRequired = ErrorMessage(
        "The teams_channel_id cannot be None or empty",
        -60208,
        "teams-integration",
    )

    TeamsConversationIdRequired = ErrorMessage(
        "conversation_id is required.",
        -60209,
        "teams-integration",
    )

    # Hosting Errors (-60300 to -60399)
    AdapterRequired = ErrorMessage(
        "start_agent_process: adapter can't be None",
        -60300,
        "hosting-configuration",
    )

    AgentApplicationRequired = ErrorMessage(
        "start_agent_process: agent_application can't be None",
        -60301,
        "hosting-configuration",
    )

    RequestRequired = ErrorMessage(
        "CloudAdapter.process: request can't be None",
        -60302,
        "hosting-configuration",
    )

    AgentRequired = ErrorMessage(
        "CloudAdapter.process: agent can't be None",
        -60303,
        "hosting-configuration",
    )

    StreamAlreadyEnded = ErrorMessage(
        "The stream has already ended.",
        -60304,
        "streaming",
    )

    TurnContextRequired = ErrorMessage(
        "TurnContext cannot be None.",
        -60305,
        "hosting-configuration",
    )

    ActivityRequired = ErrorMessage(
        "Activity cannot be None.",
        -60306,
        "hosting-configuration",
    )

    AppIdRequired = ErrorMessage(
        "AppId cannot be empty or None.",
        -60307,
        "hosting-configuration",
    )

    InvalidActivityType = ErrorMessage(
        "Invalid or missing activity type.",
        -60308,
        "hosting-configuration",
    )

    ConversationIdRequired = ErrorMessage(
        "Conversation ID cannot be empty or None.",
        -60309,
        "hosting-configuration",
    )

    AuthHeaderRequired = ErrorMessage(
        "Authorization header is required.",
        -60310,
        "hosting-configuration",
    )

    InvalidAuthHeader = ErrorMessage(
        "Invalid authorization header format.",
        -60311,
        "hosting-configuration",
    )

    ClaimsIdentityRequired = ErrorMessage(
        "ClaimsIdentity is required.",
        -60312,
        "hosting-configuration",
    )

    ChannelServiceRouteNotFound = ErrorMessage(
        "Channel service route not found for: {0}",
        -60313,
        "hosting-configuration",
    )

    TokenExchangeRequired = ErrorMessage(
        "Token exchange requires a token exchange resource.",
        -60314,
        "hosting-configuration",
    )

    MissingHttpClient = ErrorMessage(
        "HTTP client is required.",
        -60315,
        "hosting-configuration",
    )

    InvalidBotFrameworkActivity = ErrorMessage(
        "Invalid Bot Framework Activity format.",
        -60316,
        "hosting-configuration",
    )

    CredentialsRequired = ErrorMessage(
        "Credentials are required for authentication.",
        -60317,
        "hosting-configuration",
    )

    # Activity Errors (-60400 to -60499)
    InvalidChannelIdType = ErrorMessage(
        "Invalid type for channel_id: {0}. Expected ChannelId or str.",
        -60400,
        "activity-schema",
    )

    ChannelIdProductInfoConflict = ErrorMessage(
        "Conflict between channel_id.sub_channel and productInfo entity",
        -60401,
        "activity-schema",
    )

    ChannelIdValueConflict = ErrorMessage(
        "If value is provided, channel and sub_channel must be None",
        -60402,
        "activity-schema",
    )

    ChannelIdValueMustBeNonEmpty = ErrorMessage(
        "value must be a non empty string if provided",
        -60403,
        "activity-schema",
    )

    InvalidFromPropertyType = ErrorMessage(
        "Invalid type for from_property: {0}. Expected ChannelAccount or dict.",
        -60404,
        "activity-schema",
    )

    InvalidRecipientType = ErrorMessage(
        "Invalid type for recipient: {0}. Expected ChannelAccount or dict.",
        -60405,
        "activity-schema",
    )

    # Copilot Studio Errors (-60500 to -60599)
    CloudBaseAddressRequired = ErrorMessage(
        "cloud_base_address must be provided when PowerPlatformCloud is Other",
        -60500,
        "copilot-studio-client",
    )

    EnvironmentIdRequired = ErrorMessage(
        "EnvironmentId must be provided",
        -60501,
        "copilot-studio-client",
    )

    AgentIdentifierRequired = ErrorMessage(
        "AgentIdentifier must be provided",
        -60502,
        "copilot-studio-client",
    )

    CustomCloudOrBaseAddressRequired = ErrorMessage(
        "Either CustomPowerPlatformCloud or cloud_base_address must be provided when PowerPlatformCloud is Other",
        -60503,
        "copilot-studio-client",
    )

    InvalidConnectionSettingsType = ErrorMessage(
        "connection_settings must be of type DirectToEngineConnectionSettings",
        -60504,
        "copilot-studio-client",
    )

    PowerPlatformEnvironmentRequired = ErrorMessage(
        "PowerPlatformEnvironment must be provided",
        -60505,
        "copilot-studio-client",
    )

    AccessTokenProviderRequired = ErrorMessage(
        "AccessTokenProvider must be provided",
        -60506,
        "copilot-studio-client",
    )

    # General/Validation Errors (-60600 to -60699)
    InvalidConfiguration = ErrorMessage(
        "Invalid configuration: {0}",
        -60600,
        "configuration",
    )

    RequiredParameterMissing = ErrorMessage(
        "Required parameter missing: {0}",
        -60601,
        "configuration",
    )

    InvalidParameterValue = ErrorMessage(
        "Invalid parameter value for {0}: {1}",
        -60602,
        "configuration",
    )

    OperationNotSupported = ErrorMessage(
        "Operation not supported: {0}",
        -60603,
        "configuration",
    )

    ResourceNotFound = ErrorMessage(
        "Resource not found: {0}",
        -60604,
        "configuration",
    )

    UnexpectedError = ErrorMessage(
        "An unexpected error occurred: {0}",
        -60605,
        "configuration",
    )

    InvalidStateObject = ErrorMessage(
        "Invalid state object: {0}",
        -60606,
        "configuration",
    )

    SerializationError = ErrorMessage(
        "Serialization error: {0}",
        -60607,
        "configuration",
    )

    DeserializationError = ErrorMessage(
        "Deserialization error: {0}",
        -60608,
        "configuration",
    )

    TimeoutError = ErrorMessage(
        "Operation timed out: {0}",
        -60609,
        "configuration",
    )

    NetworkError = ErrorMessage(
        "Network error occurred: {0}",
        -60610,
        "configuration",
    )

    def __init__(self):
        """Initialize ErrorResources singleton."""
        pass

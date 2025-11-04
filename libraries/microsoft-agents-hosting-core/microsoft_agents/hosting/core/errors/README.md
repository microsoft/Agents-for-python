# Error Resources for Microsoft Agents SDK

This module provides centralized error messages with error codes and help URLs for the Microsoft Agents SDK, following the pattern established in the C# SDK.

## Overview

All error messages in the Microsoft Agents SDK are now centralized in the `error_resources` module. Each error includes:

1. **Formatted message string** - Can include placeholders for dynamic values
2. **Error code** - A unique negative integer identifying the error
3. **Help URL** - A link to documentation with hashtag anchor

## Usage

### Basic Usage

```python
from microsoft_agents.hosting.core import error_resources

# Raise an error with a simple message
raise ValueError(str(error_resources.CosmosDbConfigRequired))

# Raise an error with formatted arguments
raise ValueError(error_resources.FailedToAcquireToken.format(auth_payload))

# Multiple arguments
raise ValueError(error_resources.CosmosDbPartitionKeyInvalid.format(key1, key2))
```

### Example Output

When an error is raised, it will look like:

```
Failed to acquire token. {'error': 'invalid_grant'}

Error Code: -60012
Help URL: https://aka.ms/M365AgentsErrorCodes/#agentic-identity-with-the-m365-agents-sdk
```

## Error Code Ranges

Error codes are organized by category in the following ranges:

| Range | Category | Example |
|-------|----------|---------|
| -60000 to -60099 | Authentication | FailedToAcquireToken (-60012) |
| -60100 to -60199 | Storage | CosmosDbConfigRequired (-60100) |
| -60200 to -60299 | Teams | TeamsBadRequest (-60200) |
| -60300 to -60399 | Hosting | AdapterRequired (-60300) |
| -60400 to -60499 | Activity | InvalidChannelIdType (-60400) |
| -60500 to -60599 | Copilot Studio | CloudBaseAddressRequired (-60500) |
| -60600 to -60699 | General/Validation | InvalidConfiguration (-60600) |

## Available Error Resources

### Authentication Errors

- `FailedToAcquireToken` - Failed to acquire authentication token
- `InvalidInstanceUrl` - Invalid instance URL provided
- `OnBehalfOfFlowNotSupportedManagedIdentity` - On-behalf-of flow not supported with managed identity
- `OnBehalfOfFlowNotSupportedAuthType` - On-behalf-of flow not supported with current auth type
- `AuthenticationTypeNotSupported` - Authentication type not supported
- `AgentApplicationInstanceIdRequired` - Agent application instance ID required
- `FailedToAcquireAgenticInstanceToken` - Failed to acquire agentic instance token
- `AgentApplicationInstanceIdAndUserIdRequired` - Both agent app instance ID and user ID required
- `FailedToAcquireInstanceOrAgentToken` - Failed to acquire instance or agent token

### Storage Errors

- `CosmosDbConfigRequired` - CosmosDB configuration required
- `CosmosDbEndpointRequired` - CosmosDB endpoint required
- `CosmosDbAuthKeyRequired` - CosmosDB auth key required
- `CosmosDbDatabaseIdRequired` - CosmosDB database ID required
- `CosmosDbContainerIdRequired` - CosmosDB container ID required
- `CosmosDbKeyCannotBeEmpty` - CosmosDB key cannot be empty
- `BlobStorageConfigRequired` - Blob storage configuration required
- `BlobContainerNameRequired` - Blob container name required
- `StorageKeyCannotBeEmpty` - Storage key cannot be empty

### Teams Errors

- `TeamsBadRequest` - Bad request
- `TeamsNotImplemented` - Not implemented
- `TeamsContextRequired` - Context required
- `TeamsMeetingIdRequired` - Meeting ID required
- `TeamsParticipantIdRequired` - Participant ID required
- `TeamsTeamIdRequired` - Team ID required
- `TeamsTurnContextRequired` - TurnContext required
- `TeamsActivityRequired` - Activity required
- `TeamsChannelIdRequired` - Teams channel ID required
- `TeamsConversationIdRequired` - Conversation ID required

### Hosting Errors

- `AdapterRequired` - Adapter required
- `AgentApplicationRequired` - Agent application required
- `RequestRequired` - Request required
- `AgentRequired` - Agent required
- `StreamAlreadyEnded` - Stream already ended
- `TurnContextRequired` - TurnContext required
- `ActivityRequired` - Activity required

### Activity Errors

- `InvalidChannelIdType` - Invalid channel ID type
- `ChannelIdProductInfoConflict` - Conflict between channel ID and product info
- `ChannelIdValueConflict` - Value and channel cannot both be provided
- `ChannelIdValueMustBeNonEmpty` - Channel ID value must be non-empty

### Copilot Studio Errors

- `CloudBaseAddressRequired` - Cloud base address required
- `EnvironmentIdRequired` - Environment ID required
- `AgentIdentifierRequired` - Agent identifier required
- `CustomCloudOrBaseAddressRequired` - Custom cloud or base address required
- `PowerPlatformEnvironmentRequired` - Power Platform environment required
- `AccessTokenProviderRequired` - Access token provider required

### General/Validation Errors

- `InvalidConfiguration` - Invalid configuration
- `RequiredParameterMissing` - Required parameter missing
- `InvalidParameterValue` - Invalid parameter value
- `OperationNotSupported` - Operation not supported
- `ResourceNotFound` - Resource not found
- `UnexpectedError` - Unexpected error occurred

## Adding New Error Messages

To add a new error message:

1. Open `error_resources.py`
2. Add a new `ErrorMessage` instance to the `ErrorResources` class
3. Follow the naming convention: `PascalCaseErrorName`
4. Assign an error code in the appropriate range
5. Provide an appropriate help URL anchor

Example:

```python
NewErrorType = ErrorMessage(
    "Description of the error with {0} placeholder",
    -60XXX,  # Use appropriate range
    "help-url-anchor",
)
```

## Avoiding Circular Imports

When using error_resources in modules that are imported by hosting-core's `__init__.py`, use lazy imports to avoid circular dependencies:

```python
# Instead of module-level import:
# from microsoft_agents.hosting.core import error_resources

# Use lazy import where needed:
def my_function():
    from microsoft_agents.hosting.core import error_resources
    raise ValueError(str(error_resources.SomeError))
```

## Testing

Tests for error resources are located in `tests/hosting_core/errors/test_error_resources.py`.

To run tests:
```bash
pytest tests/hosting_core/errors/test_error_resources.py -v
```

## Contributing

When refactoring existing error messages:

1. Find the error message in the code
2. Identify or create an appropriate error resource
3. Replace the hardcoded string with `str(error_resources.ErrorName)` or `error_resources.ErrorName.format(args)`
4. For errors with placeholders, use `.format()` with appropriate arguments
5. Update tests if needed

## Future Work

- Help URLs will be updated with correct deep-link hashtags once documentation is available
- Additional error messages can be added as needed
- Error codes can be aligned with C# SDK as that evolves

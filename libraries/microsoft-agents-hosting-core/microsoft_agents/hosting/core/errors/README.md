# Error Resources for Microsoft Agents SDK - Hosting Core

This module provides centralized error messages with error codes and help URLs for hosting operations in the Microsoft Agents SDK.

## Overview

Error messages are organized by package, with each package maintaining its own error resources:

- **Authentication** (`microsoft-agents-authentication-msal`): -60000 to -60999
- **Storage - Cosmos** (`microsoft-agents-storage-cosmos`): -61000 to -61999
- **Storage - Blob** (`microsoft-agents-storage-blob`): -61100 to -61199
- **Teams** (`microsoft-agents-hosting-teams`): -62000 to -62999
- **Hosting** (`microsoft-agents-hosting-core`): -63000 to -63999
- **Activity** (`microsoft-agents-activity`): -64000 to -64999
- **Copilot Studio** (`microsoft-agents-copilotstudio-client`): -65000 to -65999
- **General/Validation** (`microsoft-agents-hosting-core`): -66000 to -66999

## Usage

### Hosting Core Errors

```python
from microsoft_agents.hosting.core import error_resources

# Raise an error with a simple message
raise ValueError(str(error_resources.AdapterRequired))

# Raise an error with formatted arguments
raise ValueError(error_resources.ChannelServiceRouteNotFound.format("route_name"))
```

### Package-Specific Errors

Each package exports its own error resources:

```python
# Authentication errors
from microsoft_agents.authentication.msal.errors import authentication_errors
raise ValueError(authentication_errors.FailedToAcquireToken.format(payload))

# Storage errors
from microsoft_agents.storage.cosmos.errors import storage_errors
raise ValueError(str(storage_errors.CosmosDbConfigRequired))

# Teams errors
from microsoft_agents.hosting.teams.errors import teams_errors
raise ValueError(str(teams_errors.TeamsContextRequired))

# Activity errors
from microsoft_agents.activity.errors import activity_errors
raise ValueError(activity_errors.InvalidChannelIdType.format(type(value)))

# Copilot Studio errors
from microsoft_agents.copilotstudio.client.errors import copilot_studio_errors
raise ValueError(str(copilot_studio_errors.EnvironmentIdRequired))
```

## Example Output

When an error is raised, it will look like:

```
Failed to acquire token. {'error': 'invalid_grant'}

Error Code: -60012
Help URL: https://aka.ms/M365AgentsErrorCodes/#agentic-identity-with-the-m365-agents-sdk
```

## Error Code Ranges

| Range | Package | Category | Example |
|-------|---------|----------|---------|
| -60000 to -60999 | microsoft-agents-authentication-msal | Authentication | FailedToAcquireToken (-60012) |
| -61000 to -61999 | microsoft-agents-storage-cosmos | Storage (Cosmos) | CosmosDbConfigRequired (-61000) |
| -61100 to -61199 | microsoft-agents-storage-blob | Storage (Blob) | BlobStorageConfigRequired (-61100) |
| -62000 to -62999 | microsoft-agents-hosting-teams | Teams | TeamsBadRequest (-62000) |
| -63000 to -63999 | microsoft-agents-hosting-core | Hosting | AdapterRequired (-63000) |
| -64000 to -64999 | microsoft-agents-activity | Activity | InvalidChannelIdType (-64000) |
| -65000 to -65999 | microsoft-agents-copilotstudio-client | Copilot Studio | CloudBaseAddressRequired (-65000) |
| -66000 to -66999 | microsoft-agents-hosting-core | General/Validation | InvalidConfiguration (-66000) |

## Adding New Error Messages

To add a new error message to a package:

1. Navigate to the package's `errors/error_resources.py` file
2. Add a new `ErrorMessage` instance with an appropriate error code within the package's range
3. Follow the naming convention: `PascalCaseErrorName`
4. Provide an appropriate help URL anchor

Example:

```python
NewHostingError = ErrorMessage(
    "Description of the error with {0} placeholder",
    -63XXX,  # Use next available code in hosting range
    "help-url-anchor",
)
```

## Avoiding Circular Imports

When using error resources in modules that might cause circular dependencies, use lazy imports:

```python
def my_function():
    from microsoft_agents.activity.errors import activity_errors
    raise ValueError(str(activity_errors.SomeError))
```

## Testing

Tests for error resources are located in `tests/hosting_core/errors/test_error_resources.py` and package-specific test files.

## Contributing

When refactoring existing error messages:

1. Identify the package where the error belongs
2. Find or create the appropriate error resource in that package
3. Replace hardcoded strings with the error resource reference
4. Format with Black
5. Update tests if needed

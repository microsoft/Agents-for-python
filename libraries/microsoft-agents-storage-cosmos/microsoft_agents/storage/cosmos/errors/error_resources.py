# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Storage error resources for Microsoft Agents SDK (CosmosDB).

Error codes are in the range -61000 to -61999.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage


class StorageErrorResources:
    """
    Error messages for storage operations (CosmosDB).

    Error codes are organized in the range -61000 to -61999.
    """

    CosmosDbConfigRequired = ErrorMessage(
        "CosmosDBStorage: CosmosDBConfig is required.",
        -61000,
    )

    CosmosDbEndpointRequired = ErrorMessage(
        "CosmosDBStorage: cosmos_db_endpoint is required.",
        -61001,
    )

    CosmosDbAuthKeyRequired = ErrorMessage(
        "CosmosDBStorage: auth_key is required.",
        -61002,
    )

    CosmosDbDatabaseIdRequired = ErrorMessage(
        "CosmosDBStorage: database_id is required.",
        -61003,
    )

    CosmosDbContainerIdRequired = ErrorMessage(
        "CosmosDBStorage: container_id is required.",
        -61004,
    )

    CosmosDbKeyCannotBeEmpty = ErrorMessage(
        "CosmosDBStorage: Key cannot be empty.",
        -61005,
    )

    CosmosDbPartitionKeyInvalid = ErrorMessage(
        "CosmosDBStorage: PartitionKey of {0} cannot be used with a CosmosDbPartitionedStorageOptions.PartitionKey of {1}.",
        -61006,
    )

    CosmosDbPartitionKeyPathInvalid = ErrorMessage(
        "CosmosDBStorage: PartitionKeyPath must match cosmosDbPartitionedStorageOptions value of {0}",
        -61007,
    )

    CosmosDbCompatibilityModeRequired = ErrorMessage(
        "CosmosDBStorage: compatibilityMode cannot be set when using partitionKey options.",
        -61008,
    )

    CosmosDbPartitionKeyNotFound = ErrorMessage(
        "CosmosDBStorage: Partition key '{0}' missing from state, you may be missing custom state implementation.",
        -61009,
    )

    CosmosDbInvalidPartitionKeyValue = ErrorMessage(
        "CosmosDBStorage: Invalid PartitionKey property on item with id {0}",
        -61010,
    )

    CosmosDbInvalidKeySuffixCharacters = ErrorMessage(
        "Cannot use invalid Row Key characters: {0} in keySuffix.",
        -61011,
    )

    InvalidConfiguration = ErrorMessage(
        "Invalid configuration: {0}",
        -61012,
    )

    def __init__(self):
        """Initialize StorageErrorResources."""
        pass

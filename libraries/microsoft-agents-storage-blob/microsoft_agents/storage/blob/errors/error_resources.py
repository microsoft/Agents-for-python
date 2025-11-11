# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Blob storage error resources for Microsoft Agents SDK.

Error codes are in the range -61100 to -61199.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage


class BlobStorageErrorResources:
    """
    Error messages for blob storage operations.

    Error codes are organized in the range -61100 to -61199.
    """

    BlobStorageConfigRequired = ErrorMessage(
        "BlobStorage: BlobStorageConfig is required.",
        -61100,
    )

    BlobConnectionStringOrUrlRequired = ErrorMessage(
        "BlobStorage: either connection_string or container_url is required.",
        -61101,
    )

    BlobContainerNameRequired = ErrorMessage(
        "BlobStorage: container_name is required.",
        -61102,
    )

    InvalidConfiguration = ErrorMessage(
        "Invalid configuration: {0}",
        -61103,
    )

    def __init__(self):
        """Initialize BlobStorageErrorResources."""
        pass

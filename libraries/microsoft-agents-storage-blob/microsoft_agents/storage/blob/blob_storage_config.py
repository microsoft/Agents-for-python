from typing import Generic

from azure.core.credentials_async import AsyncTokenCredential
from microsoft_agents.hosting.core.storage import StorageVersion, StorageVersionT


class BlobStorageConfig(Generic[StorageVersionT]):
    """Configuration settings for BlobStorage."""

    def __init__(
        self,
        container_name: str,
        connection_string: str = "",
        url: str = "",
        credential: AsyncTokenCredential | None = None,
        storage_version: StorageVersionT = StorageVersion.V1,
    ):
        """Configuration settings for BlobStorage.

        container_name: The name of the blob container.
        connection_string: The connection string to the storage account.
        url: The URL of the blob service. If provided, credential must also be provided.
        credential: The TokenCredential to use for authentication when using a custom URL.

        credential-based authentication is prioritized over connection string authentication.
        """
        self.container_name: str = container_name
        self.connection_string: str = connection_string
        self.url: str = url
        self.credential: AsyncTokenCredential | None = credential
        self.storage_version = StorageVersion(storage_version)

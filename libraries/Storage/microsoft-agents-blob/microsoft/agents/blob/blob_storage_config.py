from typing import Union

from azure.core.credentials import TokenCredential


class BlobStorageConfig:
    """Configuration settings for BlobStorage."""

    def __init__(
        self,
        container_name: str,
        connection_string: str = "",
        url: str = "",
        credential: Union[TokenCredential, None] = None,
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
        self.credential: Union[TokenCredential, None] = credential

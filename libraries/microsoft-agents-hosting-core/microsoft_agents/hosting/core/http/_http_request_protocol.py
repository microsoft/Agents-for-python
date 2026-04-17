# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol for abstracting HTTP request objects across frameworks."""

from typing import Protocol, Any


class HttpRequestProtocol(Protocol):
    """Protocol for HTTP requests that adapters must implement.

    This protocol defines the interface that framework-specific request
    adapters must implement to work with the shared HTTP adapter logic.
    """

    @property
    def method(self) -> str:
        """HTTP method (GET, POST, etc.)."""
        ...

    @property
    def headers(self) -> dict[str, str]:
        """Request headers."""
        ...

    async def json(self) -> dict[str, Any]:
        """Parse request body as JSON."""
        ...

    def get_claims_identity(self) -> Any | None:
        """Get claims identity attached by auth middleware."""
        ...

    def get_path_param(self, name: str) -> str:
        """Get path parameter by name."""
        ...

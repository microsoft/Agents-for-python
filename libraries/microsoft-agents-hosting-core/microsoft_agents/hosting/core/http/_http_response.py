# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""HTTP response abstraction."""

from typing import Any, Optional, Dict
from dataclasses import dataclass


@dataclass
class HttpResponse:
    """Framework-agnostic HTTP response."""

    status_code: int
    body: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    content_type: Optional[str] = "application/json"


class HttpResponseFactory:
    """Factory for creating HTTP responses."""

    @staticmethod
    def ok(body: Any = None) -> HttpResponse:
        """Create 200 OK response."""
        return HttpResponse(status_code=200, body=body)

    @staticmethod
    def accepted() -> HttpResponse:
        """Create 202 Accepted response."""
        return HttpResponse(status_code=202)

    @staticmethod
    def json(body: Any, status_code: int = 200) -> HttpResponse:
        """Create JSON response."""
        return HttpResponse(status_code=status_code, body=body)

    @staticmethod
    def bad_request(message: str = "Bad Request") -> HttpResponse:
        """Create 400 Bad Request response."""
        return HttpResponse(status_code=400, body={"error": message})

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> HttpResponse:
        """Create 401 Unauthorized response."""
        return HttpResponse(status_code=401, body={"error": message})

    @staticmethod
    def method_not_allowed(message: str = "Method Not Allowed") -> HttpResponse:
        """Create 405 Method Not Allowed response."""
        return HttpResponse(status_code=405, body={"error": message})

    @staticmethod
    def unsupported_media_type(message: str = "Unsupported Media Type") -> HttpResponse:
        """Create 415 Unsupported Media Type response."""
        return HttpResponse(status_code=415, body={"error": message})

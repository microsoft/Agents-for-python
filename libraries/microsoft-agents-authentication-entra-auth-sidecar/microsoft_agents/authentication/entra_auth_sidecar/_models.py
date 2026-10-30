# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .connection_settings import SidecarConnectionSettings
from .constants import (
    DEFAULT_SERVICE_NAME,
    DEFAULT_BLUEPRINT_SERVICE_NAME,
    DEFAULT_SIDECAR_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_COUNT,
)

__all__ = [
    "SidecarConnectionSettings",
    "SidecarRequestOptions",
    "SidecarTokenResult",
    "SidecarProblemDetails",
    "DEFAULT_SERVICE_NAME",
    "DEFAULT_BLUEPRINT_SERVICE_NAME",
    "DEFAULT_SIDECAR_BASE_URL",
    "DEFAULT_REQUEST_TIMEOUT_SECONDS",
    "DEFAULT_RETRY_COUNT",
]


class SidecarRequestOptions:
    """Options used to build the query string for a sidecar token request."""

    def __init__(
        self,
        *,
        agent_identity: str | None = None,
        agent_username: str | None = None,
        agent_user_id: str | None = None,
        scopes: list[str] | None = None,
        request_app_token: bool | None = None,
        tenant: str | None = None,
        force_refresh: bool | None = None,
    ):
        # Agent app (client) ID for agent identity flows. Maps to ``AgentIdentity``.
        self.agent_identity = agent_identity
        # Agentic user principal name. Maps to ``AgentUsername``.
        self.agent_username = agent_username
        # Agentic user object ID. Maps to ``AgentUserId``.
        self.agent_user_id = agent_user_id
        # Override the configured downstream API scopes. Maps to ``optionsOverride.Scopes``.
        # Normalize once at this boundary (trim, drop blanks) so downstream URL
        # building and cache-key construction can treat scopes as a clean list.
        self.scopes = (
            ([s.strip() for s in scopes if s and s.strip()] or None) if scopes else None
        )
        # Request an app-only token. Maps to ``optionsOverride.RequestAppToken=true``.
        self.request_app_token = request_app_token
        # Override the tenant. Maps to ``optionsOverride.AcquireTokenOptions.Tenant``.
        self.tenant = tenant
        # Force a fresh acquisition, bypassing the sidecar cache.
        # Maps to ``optionsOverride.AcquireTokenOptions.ForceRefresh=true``.
        self.force_refresh = force_refresh


class SidecarTokenResult:
    """Result of a successful sidecar token acquisition."""

    def __init__(self, scheme: str, token: str):
        # The authorization scheme (e.g., "Bearer" or "PoP").
        self.scheme = scheme
        # The raw access token.
        self.token = token


class SidecarProblemDetails:
    """RFC 7807 ProblemDetails parsed from sidecar error responses."""

    def __init__(
        self,
        *,
        type: str | None = None,
        title: str | None = None,
        status: int | None = None,
        detail: str | None = None,
        instance: str | None = None,
    ):
        self.type = type
        self.title = title
        self.status = status
        self.detail = detail
        self.instance = instance

    @classmethod
    def from_dict(cls, data: dict) -> "SidecarProblemDetails":
        return cls(
            type=data.get("type"),
            title=data.get("title"),
            status=data.get("status"),
            detail=data.get("detail"),
            instance=data.get("instance"),
        )

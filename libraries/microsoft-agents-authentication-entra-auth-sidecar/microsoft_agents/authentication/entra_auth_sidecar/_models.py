# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from microsoft_agents.activity.config._coercion import (
    coerce_bool,
    coerce_int,
    coerce_float,
)
from microsoft_agents.hosting.core import ConnectionSettingsBase

DEFAULT_SERVICE_NAME = "default"
DEFAULT_BLUEPRINT_SERVICE_NAME = "agenticblueprint"
DEFAULT_SIDECAR_BASE_URL = "http://localhost:5178"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30.0
DEFAULT_RETRY_COUNT = 3


class SidecarConnectionSettings(ConnectionSettingsBase):
    """
    Connection settings for the sidecar-based token provider.

    Extends :class:`microsoft_agents.hosting.core.ConnectionSettingsBase` with the
    sidecar-specific fields, mirroring the .NET
    ``Microsoft.Agents.Authentication.EntraAuthSidecar.SidecarConnectionSettings``
    which derives from ``ConnectionSettingsBase``. Bound from an
    :class:`microsoft_agents.hosting.core.AgentAuthConfiguration` (or its raw
    ``SETTINGS`` keyword arguments). No secrets/certificates are required: the
    sidecar owns all credential management.
    """

    def __init__(
        self,
        *,
        service_name: str | None = None,
        blueprint_service_name: str | None = None,
        sidecar_base_url: str | None = None,
        bypass_local_network_restriction: bool = False,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        retry_count: int = DEFAULT_RETRY_COUNT,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        tenant_id: str | None = None,
        authority: str | None = None,
        alternate_blueprint_connection_name: str | None = None,
    ):
        super().__init__(
            client_id=client_id,
            authority=authority,
            tenant_id=tenant_id,
            scopes=self._normalize_scopes(scopes),
            alternate_blueprint_connection_name=alternate_blueprint_connection_name,
        )
        # An explicitly blank value (e.g. binding yields "") must never produce an
        # invalid sidecar endpoint path, so normalize to the defaults here.
        self.service_name = service_name or DEFAULT_SERVICE_NAME
        self.blueprint_service_name = (
            blueprint_service_name or DEFAULT_BLUEPRINT_SERVICE_NAME
        )
        self.sidecar_base_url = sidecar_base_url
        # Config values can arrive as strings from ``load_configuration_from_env``,
        # so coerce explicitly: ``bool("false")`` would otherwise be ``True`` and
        # silently disable the SSRF guard, and ``max(0, "5")`` would raise.
        self.bypass_local_network_restriction = coerce_bool(
            bypass_local_network_restriction
        )
        self.request_timeout = coerce_float(
            request_timeout, DEFAULT_REQUEST_TIMEOUT_SECONDS, "REQUEST_TIMEOUT"
        )
        self.retry_count = coerce_int(retry_count, DEFAULT_RETRY_COUNT, "RETRY_COUNT")

    @staticmethod
    def _normalize_scopes(scopes) -> list[str] | None:
        """Normalize scopes to a list of strings.

        Accepts a list, a string (space/comma-delimited), or a dict (produced when
        scopes are supplied via env as ``SCOPES__0=...`` and parsed into
        ``{"0": "..."}``). Returns ``None`` when no scopes are present.
        """
        if scopes is None:
            return None
        if isinstance(scopes, str):
            parts = [s.strip() for s in scopes.replace(",", " ").split()]
            return [s for s in parts if s] or None
        if isinstance(scopes, dict):
            scopes = scopes.values()
        result = [str(s).strip() for s in scopes if s and str(s).strip()]
        return result or None

    @classmethod
    def from_configuration(cls, configuration) -> "SidecarConnectionSettings":
        """
        Build settings from an :class:`AgentAuthConfiguration`.

        Reads sidecar-specific values from the configuration object when present,
        tolerating both attribute-style and the SDK's upper-case kwargs style.
        """

        def _get(*names, default=None):
            for name in names:
                value = getattr(configuration, name, None)
                if value is not None:
                    return value
            return default

        return cls(
            service_name=_get("SERVICE_NAME", "service_name"),
            blueprint_service_name=_get(
                "BLUEPRINT_SERVICE_NAME", "blueprint_service_name"
            ),
            sidecar_base_url=_get("SIDECAR_BASE_URL", "sidecar_base_url"),
            bypass_local_network_restriction=_get(
                "BYPASS_LOCAL_NETWORK_RESTRICTION",
                "bypass_local_network_restriction",
                default=False,
            ),
            request_timeout=_get(
                "REQUEST_TIMEOUT",
                "request_timeout",
                default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            ),
            retry_count=_get("RETRY_COUNT", "retry_count", default=DEFAULT_RETRY_COUNT),
            scopes=_get("SCOPES", "scopes"),
            client_id=_get("CLIENT_ID", "client_id"),
            tenant_id=_get("TENANT_ID", "tenant_id"),
            authority=_get("AUTHORITY", "authority"),
            alternate_blueprint_connection_name=_get(
                "ALT_BLUEPRINT_ID",
                "ALT_BLUEPRINT_NAME",
                "alternate_blueprint_connection_name",
            ),
        )


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
        self.scopes = scopes
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

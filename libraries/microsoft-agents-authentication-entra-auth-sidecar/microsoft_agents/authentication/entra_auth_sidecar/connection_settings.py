# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from microsoft_agents.activity.config import (
    Configuration,
    xpath,
)
from microsoft_agents.hosting.core.authorization.connection_settings_base import (
    _ConnectionSettingsBase,
)
from .constants import (
    DEFAULT_SERVICE_NAME,
    DEFAULT_BLUEPRINT_SERVICE_NAME,
    DEFAULT_SIDECAR_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_COUNT,
)

@dataclass(frozen=True)
class SidecarConnectionSettings(_ConnectionSettingsBase):
    """
    Connection settings for the sidecar-based token provider.

    Extends
    :class:`microsoft_agents.hosting.core.authorization.connection_settings_base._ConnectionSettingsBase`
    with the sidecar-specific fields, mirroring the .NET
    ``Microsoft.Agents.Authentication.EntraAuthSidecar.SidecarConnectionSettings``
    which derives from ``_ConnectionSettingsBase``. Bound from an
    :class:`microsoft_agents.hosting.core.AgentAuthConfiguration` (or its raw
    ``SETTINGS`` keyword arguments). No secrets/certificates are required: the
    sidecar owns all credential management.
    """

    service_name: str | None = None
    blueprint_service_name: str | None = None
    sidecar_base_url: str | None = None
    bypass_local_network_restriction: bool = False
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    retry_count: int = DEFAULT_RETRY_COUNT


    def __init__(
        self,
        *args,
        service_name: str | None = None,
        blueprint_service_name: str | None = None,
        sidecar_base_url: str | None = None,
        bypass_local_network_restriction: bool = False,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        retry_count: int = DEFAULT_RETRY_COUNT,
        **kwargs,
    ):
        service_name = (service_name or "").strip() or DEFAULT_SERVICE_NAME
        blueprint_service_name = (blueprint_service_name or "").strip() or DEFAULT_BLUEPRINT_SERVICE_NAME

        super().__init__(
            client_id=client_id,
            authority=authority,
            tenant_id=tenant_id,
            scopes=self._normalize_scopes(scopes),
            alternate_blueprint_connection_name=alternate_blueprint_connection_name,
        )
        # An explicitly blank or whitespace-only value (e.g. binding yields "" or
        # "   ") must never produce an invalid sidecar endpoint path, so strip and
        # normalize to the defaults here.
        self.service_name = (service_name or "").strip() or DEFAULT_SERVICE_NAME
        self.blueprint_service_name = (
            blueprint_service_name or ""
        ).strip() or DEFAULT_BLUEPRINT_SERVICE_NAME
        self.sidecar_base_url = sidecar_base_url
        # Config values can arrive as strings from ``load_configuration_from_env``,
        # so coerce explicitly: ``bool("false")`` would otherwise be ``True`` and
        # silently disable the SSRF guard, and ``max(0, "5")`` would raise.
        self.bypass_local_network_restriction = coerce_bool(
            bypass_local_network_restriction,
            default=False,
            name="BYPASS_LOCAL_NETWORK_RESTRICTION",
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
    def from_configuration(cls, config: Configuration) -> SidecarConnectionSettings:
        return cls(
            service_name=
        )

    @classmethod
    def from_configuration(cls, configuration) -> "SidecarConnectionSettings":
        """
        Build settings from an :class:`AgentAuthConfiguration` (or a raw SETTINGS
        mapping).

        The common base fields (client id, authority, tenant, scopes, alternate
        blueprint) are bound via
        :meth:`_ConnectionSettingsBase.base_kwargs_from_configuration` so the
        shared alias handling lives in one place; only the sidecar-specific
        fields are read here. Both attribute-style configuration objects and raw
        mappings are tolerated.
        """
        base_kwargs = cls.base_kwargs_from_configuration(configuration)

        is_mapping = isinstance(configuration, Mapping)
        extras = getattr(configuration, "provider_settings", None) or {}

        def _get(*names, default=None):
            for name in names:
                value = (
                    configuration.get(name)
                    if is_mapping
                    else getattr(configuration, name, None)
                )
                if value is None:
                    value = extras.get(name)
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
            **base_kwargs,
        )

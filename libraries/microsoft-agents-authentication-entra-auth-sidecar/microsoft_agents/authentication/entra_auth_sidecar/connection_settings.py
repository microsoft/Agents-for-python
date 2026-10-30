# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing_extensions import Self

from microsoft_agents.activity.config import Configuration, xpath
from microsoft_agents.activity.config._coercion import (
    coerce_bool,
    coerce_int,
    coerce_float,
)
from microsoft_agents.hosting.core.authorization.connections import (
    AgentAuthConfiguration,
    ConnectionSettingsBase,
)

from .constants import (
    DEFAULT_SERVICE_NAME,
    DEFAULT_BLUEPRINT_SERVICE_NAME,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_COUNT,
)


@dataclass(frozen=True)
class SidecarConnectionSettings(ConnectionSettingsBase):
    """Typed connection settings for the credential-free sidecar provider."""

    service_name: str = DEFAULT_SERVICE_NAME
    blueprint_service_name: str = DEFAULT_BLUEPRINT_SERVICE_NAME
    sidecar_base_url: str | None = None
    bypass_local_network_restriction: bool = False
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    retry_count: int = DEFAULT_RETRY_COUNT

    def __post_init__(self):
        object.__setattr__(
            self,
            "service_name",
            (self.service_name or "").strip() or DEFAULT_SERVICE_NAME,
        )
        object.__setattr__(
            self,
            "blueprint_service_name",
            (self.blueprint_service_name or "").strip()
            or DEFAULT_BLUEPRINT_SERVICE_NAME,
        )
        object.__setattr__(self, "scopes", self._normalize_scopes(self.scopes) or [])
        object.__setattr__(
            self,
            "bypass_local_network_restriction",
            coerce_bool(
                self.bypass_local_network_restriction,
                default=False,
                name="BYPASS_LOCAL_NETWORK_RESTRICTION",
            ),
        )
        object.__setattr__(
            self,
            "request_timeout",
            coerce_float(
                self.request_timeout, DEFAULT_REQUEST_TIMEOUT_SECONDS, "REQUEST_TIMEOUT"
            ),
        )
        object.__setattr__(
            self,
            "retry_count",
            coerce_int(self.retry_count, DEFAULT_RETRY_COUNT, "RETRY_COUNT"),
        )

    @staticmethod
    def _normalize_scopes(scopes) -> list[str] | None:
        if scopes is None:
            return None
        if isinstance(scopes, str):
            scopes = scopes.replace(",", " ").split()
        if isinstance(scopes, Mapping):
            scopes = scopes.values()
        return [
            str(scope).strip() for scope in scopes if scope and str(scope).strip()
        ] or None

    @classmethod
    def from_configuration(
        cls, config: Configuration | Mapping | AgentAuthConfiguration | Self
    ) -> Self:
        if isinstance(config, AgentAuthConfiguration):
            return cls._from_agent_auth_config(config)
        if isinstance(config, Mapping):
            config = Configuration.from_mapping(config)
        return super().from_configuration(config)

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        normalized = Configuration(config, _base_path=config._base_path)
        for alias in xpath("scopes"):
            normalized.pop(alias, None)
        normalized["scopes"] = cls._normalize_scopes(config.get(xpath("scopes"))) or []
        base = super()._get_init_kwargs(normalized)
        base.update(
            {
                "service_name": config.get_strn(xpath("service_name")),
                "blueprint_service_name": config.get_strn(
                    xpath("blueprint_service_name")
                ),
                "sidecar_base_url": config.get_strn(xpath("sidecar_base_url")),
                "bypass_local_network_restriction": coerce_bool(
                    config.get(xpath("bypass_local_network_restriction")),
                    default=False,
                    name="BYPASS_LOCAL_NETWORK_RESTRICTION",
                ),
                "request_timeout": config.get_float(
                    xpath("request_timeout"), default=DEFAULT_REQUEST_TIMEOUT_SECONDS
                ),
                "retry_count": config.get_int(
                    xpath("retry_count"), default=DEFAULT_RETRY_COUNT
                ),
            }
        )
        return base

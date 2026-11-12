# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing_extensions import Self

from microsoft_agents.activity.config import (
    Configuration,
    coerce_bool,
    _legpath as legpath,
)
from microsoft_agents.hosting.core.authorization.connections import (
    AgentAuthConfiguration,
    ConnectionSettingsBase,
)
from .constants import (
    DEFAULT_SERVICE_NAME,
    DEFAULT_BLUEPRINT_SERVICE_NAME,
    DEFAULT_SIDECAR_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_COUNT,
)


def _or_default(s: str | None, default: str) -> str:
    return (s.strip() if s else None) or default


@dataclass(frozen=True)
class SidecarConnectionSettings(ConnectionSettingsBase):
    """
    Connection settings for the sidecar-based token provider.

    Extends :class:`microsoft_agents.hosting.core.ConnectionSettingsBase`.
    Construct directly or use ``from_config`` for scoped mappings,
    Configuration, an existing settings instance, or defaults. Sidecar-specific
    field matching ignores case and underscores; the shared base defines
    connection-level fields.

    The ``from_configuration`` compatibility method additionally accepts legacy
    AgentAuthConfiguration. No secrets/certificates are required: the sidecar
    owns credential management. Frozen fields do not make nested values immutable.
    """

    service_name: str | None = DEFAULT_SERVICE_NAME
    blueprint_service_name: str | None = DEFAULT_BLUEPRINT_SERVICE_NAME
    sidecar_base_url: str | None = None
    bypass_local_network_restriction: bool = False
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    retry_count: int = DEFAULT_RETRY_COUNT

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bypass_local_network_restriction",
            coerce_bool(self.bypass_local_network_restriction),
        )

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        base = super()._get_init_kwargs(config)

        # An explicitly blank or whitespace-only value (e.g. binding yields "" or
        # "   ") must never produce an invalid sidecar endpoint path, so strip and
        # normalize to the defaults here.
        _service_name = config.get_strn(legpath("service_name"))
        service_name = _or_default(_service_name, DEFAULT_SERVICE_NAME)

        blueprint_service_name = config.get_str(
            legpath("blueprint_service_name"), default=DEFAULT_BLUEPRINT_SERVICE_NAME
        )
        blueprint_service_name = _or_default(
            blueprint_service_name, DEFAULT_BLUEPRINT_SERVICE_NAME
        )

        sidecar_base_url = config.get_strn(legpath("sidecar_base_url"))

        # Config values can arrive as strings from ``load_configuration_from_env``,
        # so coerce explicitly: ``bool("false")`` would otherwise be ``True`` and
        # silently disable the SSRF guard, and ``max(0, "5")`` would raise.
        bypass_local_network_restriction = config.get_bool(
            legpath("bypass_local_network_restriction"),
            default=False,
        )
        request_timeout = config.get_float(
            legpath("request_timeout"),
            default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        )
        retry_count = config.get_int(
            legpath("retry_count"),
            default=DEFAULT_RETRY_COUNT,
        )

        base.update(
            {
                "service_name": service_name,
                "blueprint_service_name": blueprint_service_name,
                "sidecar_base_url": sidecar_base_url,
                "bypass_local_network_restriction": bypass_local_network_restriction,
                "request_timeout": request_timeout,
                "retry_count": retry_count,
            }
        )
        return base

    @classmethod
    def from_configuration(
        cls, config: Configuration | Mapping | AgentAuthConfiguration | Self
    ) -> Self:
        """Compatibility binder that also converts legacy AgentAuthConfiguration.

        Prefer ``from_config`` for mappings, Configuration, or bound settings.
        """
        if isinstance(config, AgentAuthConfiguration):
            return cls._from_agent_auth_config(config)
        if isinstance(config, Mapping):
            config = Configuration.from_config(config)
        return super().from_config(config)

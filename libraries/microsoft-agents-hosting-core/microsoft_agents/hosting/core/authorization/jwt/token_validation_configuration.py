# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from microsoft_agents.activity.config import Configuration, _Configurable, xpath

from .jwt_connection_settings import JwtConnectionSettings


@dataclass(frozen=True)
class TokenValidationConfiguration(_Configurable):
    """JWT acceptance policy and connection settings used for key discovery.

    Root input binds policy fields from ``token_validation`` and routing settings
    from sibling ``connections``. Nonempty explicit audiences take precedence;
    otherwise all configured client IDs become accepted audiences. Missing tenant
    and anonymous-access policy values inherit from ``SERVICE_CONNECTION``.
    Explicit ``anonymous_allowed=False`` disables anonymous access.

    Scoped input binds only ``tenant_id``, ``audiences``, and
    ``anonymous_allowed``; it does not discover connections outside that section.
    For programmatic token validation, construct this dataclass with
    ``connections`` and/or ``default_jwt_settings`` to supply routing as well as
    the acceptance policy.
    """

    tenant_id: str | None = None
    audiences: list[str] = field(default_factory=list)
    anonymous_allowed: bool = False
    default_jwt_settings: JwtConnectionSettings | None = None
    connections: dict[str, JwtConnectionSettings] = field(default_factory=dict)

    @classmethod
    def _from_configuration(
        cls, configuration: Configuration
    ) -> TokenValidationConfiguration:

        token_validation: Configuration = configuration
        connection_raw_items = {}

        if configuration._is_root_config:
            token_validation = configuration.get_section(
                xpath("token_validation"), default=Configuration()
            )
            connection_raw_items = configuration.get_items(xpath("connections"))

        audiences = token_validation.get_str_list(xpath("audiences"))
        tenant_id = token_validation.get_strn(xpath("tenant_id"))
        anonymous_allowed = token_validation.get_booln(xpath("anonymous_allowed"))

        connections: dict[str, JwtConnectionSettings] = {}
        for name, conf in connection_raw_items:
            connections[name] = JwtConnectionSettings.from_mapping(conf)

        update_audiences = not audiences
        update_tenant_id = not tenant_id

        default_jwt_settings: JwtConnectionSettings | None = None
        for conn_name, conn in connections.items():

            if conn_name.upper() == "SERVICE_CONNECTION":
                if update_tenant_id:
                    tenant_id = conn.tenant_id
                default_jwt_settings = conn

            if update_audiences:
                aud = conn.client_id
                if aud:
                    audiences.append(aud)

        if default_jwt_settings is not None and anonymous_allowed is None:
            anonymous_allowed = default_jwt_settings.anonymous_allowed

        return cls(
            tenant_id=tenant_id,
            audiences=audiences,
            connections=connections,
            default_jwt_settings=default_jwt_settings,
            anonymous_allowed=anonymous_allowed or False,
        )

    def validate_audience(self, aud: Any) -> bool:
        """Check a nonempty string audience against the case-insensitive allowlist."""
        if not aud or not isinstance(aud, str):
            return False
        for target_audience in self.audiences:
            if aud.lower() == target_audience.lower():
                return True
        return False

    def get_connection_settings(self, aud: Any) -> JwtConnectionSettings | None:
        """Match a valid string audience to a connection, falling back to the default.

        This selects routing only; ``validate_audience`` decides whether the
        audience is accepted. Invalid or empty audience values return None.
        """
        if not aud or not isinstance(aud, str):
            return None
        for conn in self.connections.values():
            if conn.client_id and conn.client_id.lower() == aud.lower():
                return conn
        return self.default_jwt_settings

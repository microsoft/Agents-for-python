# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from microsoft_agents.activity.config import Configuration, _Configurable, xpath

from .jwt_connection_settings import JwtConnectionSettings


@dataclass(frozen=True)
class TokenValidationConfiguration(_Configurable):
    tenant_id: str | None = None
    audiences: list[str] = field(default_factory=list)
    anonymous_allowed: bool = False
    default_jwt_settings: JwtConnectionSettings | None = None
    connections: dict[str, JwtConnectionSettings] = field(default_factory=dict)

    @classmethod
    def _from_configuration(
        cls, configuration: Configuration
    ) -> TokenValidationConfiguration:
        token_validation = configuration.get_section(
            xpath("token_validation"), default=Configuration()
        )
        audiences = token_validation.get_str_list(xpath("audiences"))
        tenant_id = token_validation.get_strn(xpath("tenant_id"))
        anonymous_allowed = token_validation.get_booln(xpath("anonymous_allowed"))

        connections: dict[str, JwtConnectionSettings] = {}
        connection_config = configuration.get_section(
            xpath("connections"), default=Configuration()
        )
        for name in connection_config:
            connections[name] = JwtConnectionSettings.from_configuration(
                connection_config.get_section(name)
            )

        update_audiences = not audiences
        update_tenant_id = not tenant_id
        default_jwt_settings: JwtConnectionSettings | None = None
        for conn_name, conn in connections.items():
            if conn_name.upper() == "SERVICE_CONNECTION":
                if update_tenant_id:
                    tenant_id = conn.tenant_id
                default_jwt_settings = conn
            if update_audiences and conn.client_id:
                audiences.append(conn.client_id)

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
        if not aud or not isinstance(aud, str):
            return False
        return any(aud.lower() == target.lower() for target in self.audiences)

    def get_connection_settings(self, aud: Any) -> JwtConnectionSettings | None:
        if not aud or not isinstance(aud, str):
            return None
        for conn in self.connections.values():
            if conn.client_id and conn.client_id.lower() == aud.lower():
                return conn
        return self.default_jwt_settings

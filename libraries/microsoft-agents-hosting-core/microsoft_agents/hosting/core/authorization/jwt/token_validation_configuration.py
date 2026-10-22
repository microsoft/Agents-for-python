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
    def _from_configuration(cls, configuration: Configuration) -> TokenValidationConfiguration:

        token_validation = configuration.get_section(xpath("token_validation"), default=Configuration())
        audiences = token_validation.collect_str("audience::*", "AUDIENCES::*")
        tenant_id = token_validation.get_str(xpath("tenant_id"))
        anonymous_allowed = token_validation.get_booln(xpath("anonymous_allowed"))

        connections: dict[str, JwtConnectionSettings] = {}
        for name, conf in configuration.get_items(xpath("connections")):
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
        if not aud or not isinstance(aud, str):
            return False
        for target_audience in self.audiences:
            if aud.lower() == target_audience.lower():
                return True
        return False

    def get_connection_settings(self, aud: Any) -> JwtConnectionSettings | None:
        if not aud or not isinstance(aud, str):
            return None
        for conn in self.connections.values():
            if conn.client_id and conn.client_id.lower() == aud.lower():
                return conn
        return self.default_jwt_settings
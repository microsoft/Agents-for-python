# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field

from microsoft_agents.activity.config import Configuration, _Configurable

@dataclass(frozen=True)
class _ConnectionMapItem(_Configurable):

    service_url: str | None = None
    audience: str | None = None
    connection: str | None = None

    @classmethod
    def from_configuration(cls, config: Configuration) -> _ConnectionMapItem:
        return _ConnectionMapItem(
            service_url=config.try_get_str("service_url", default=None),
            audience=config.get_str("audience", default=None),
            connection=config.get_str("connection", default=None)
        )

@dataclass(frozen=True)
class _ConnectionSettingsBase(_Configurable):

    client_id: str = ""
    authority: str = ""
    tenant_id: str = ""
    scopes: list[str] = field(default_factory=list)
    alternate_blueprint_connection_name: str = ""

    @classmethod
    def from_configuration(cls, config: Configuration) -> _ConnectionSettingsBase:
        return _ConnectionSettingsBase(
            client_id=config.get_str("client_id"),
            authority=config.get_str("authority"),
            tenant_id=config.get_str("tenant_id"),
            scopes=config.get_scopes("scopes"),
            alternate_blueprint_connection_name=config.get_str("alternate_blueprint_connection_name", default="")
        )
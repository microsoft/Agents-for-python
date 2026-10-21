# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing_extensions import Self

from microsoft_agents.activity.config import Configuration, _Configurable, _name_variants

from .agent_auth_configuration import AgentAuthConfiguration

_BASE_KWARGS = ["client_id", "authority", "tenant_id", "alternate_blueprint_connection_name", "scopes"]

@dataclass(frozen=True)
class _ConnectionSettingsBase(_Configurable):

    client_id: str | None
    authority: str | None
    tenant_id: str | None
    alternate_blueprint_connection_name: str | None
    scopes: list[str] = field(default_factory=list)
    _extras: Configuration = field(default_factory=Configuration)

    @property
    def extras(self) -> Configuration:
        return self._extras

    @classmethod
    def _from_agent_auth_config(cls, agent_auth_config: AgentAuthConfiguration) -> Self:
        attrs = {}
        for attr in agent_auth_config.__dict__:
            attrs[attr] = getattr(agent_auth_config, attr)
        return cls.from_mapping(attrs)

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        return {
            "client_id": config.get_strn(*_name_variants("client_id")),
            "authority": config.get_strn(*_name_variants("authority")),
            "tenant_id": config.get_strn(*_name_variants("tenant_id")),
            "scopes": config.get_scopes(*_name_variants("scopes")),
            "alternate_blueprint_connection_name": config.get_strn("alternate_blueprint_connection_name")
        }

    @classmethod
    def _known_kwargs(cls) -> list[str]:
        return [
            f.name for f in fields(cls) if f.init and f.name != "_extras"
        ]

    @classmethod
    def _get_extras(cls, config: Configuration) -> Configuration:
        known_kwargs = cls._known_kwargs()
        base = {k: v for k, v in config.items() if k not in known_kwargs}
        return Configuration(base, **base.pop("extras", {}))

    @classmethod
    def from_configuration(cls, config: Configuration) -> Self:
        return cls(**cls._get_init_kwargs(config), _extras=cls._get_extras(config))
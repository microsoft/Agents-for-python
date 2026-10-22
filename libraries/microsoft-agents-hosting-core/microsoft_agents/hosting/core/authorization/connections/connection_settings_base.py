# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TypeVar
from typing_extensions import Self

from microsoft_agents.activity.config import Configuration, _Configurable, xpath

from .agent_auth_configuration import AgentAuthConfiguration

T = TypeVar("T", bound="ConnectionSettingsBase")

_KNOWN_KWARGS_CACHE: dict[str, list[str]] = {}

@dataclass(frozen=True)
class ConnectionSettingsBase(_Configurable):
    """Provider-independent settings bound from Configuration.

    Frozen fields cannot be reassigned, but scopes and extras remain mutable.
    Treat those containers as read-only after handing settings to a provider.
    """

    client_id: str | None = None
    authority: str | None = None
    tenant_id: str | None = None
    alternate_blueprint_connection_name: str | None = None
    scopes: list[str] = field(default_factory=list)
    _extras: Configuration = field(default_factory=Configuration)

    @property
    def extras(self) -> Configuration:
        """Return unrecognized provider settings, not an immutable copy."""
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
            "client_id": config.get_strn(cls._xpath("client_id")),
            "authority": config.get_strn(cls._xpath("authority")),
            "tenant_id": config.get_strn(cls._xpath("tenant_id")),
            "scopes": config.get_scopes(cls._xpath("scopes")),
            "alternate_blueprint_connection_name": config.get_strn(
                "alt_blueprint_id", "ALT_BLUEPRINT_ID", *cls._xpath("alternate_blueprint_connection_name")
            )
        }

    @classmethod
    def _known_kwargs(cls) -> list[str]:

        if cls.__name__ in _KNOWN_KWARGS_CACHE:
            return _KNOWN_KWARGS_CACHE[cls.__name__]

        base = [
            f.name for f in fields(cls) if f.init and f.name != "_extras"
        ]
        final = []
        for n in base:
            final.extend(xpath(n))

        _KNOWN_KWARGS_CACHE[cls.__name__] = final
        return final

    @classmethod
    def _get_extras(cls, config: Configuration) -> Configuration:
        known_kwargs = cls._known_kwargs()
        base = {k: v for k, v in config.items() if k not in known_kwargs}
        return Configuration.from_mapping(base, _base_path=config._base_path, **base.pop("extras", {}))

    @classmethod
    def _from_configuration(cls, config: Configuration) -> Self:
        try:
            settings = config.get_section(xpath("settings"))
        except KeyError:
            settings = config
        return cls(**cls._get_init_kwargs(settings), _extras=cls._get_extras(settings))

    @staticmethod
    def _xpath(name: str) -> list[str]:
        return xpath(name, lower_snake=True)
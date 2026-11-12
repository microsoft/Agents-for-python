# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TypeVar
from typing_extensions import Self

from microsoft_agents.activity.config import (
    Configuration,
    _Configurable,
    _legpath as legpath,
    _netpath as netpath,
    _get_bool,
    _pop,
)

from .agent_auth_configuration import AgentAuthConfiguration

T = TypeVar("T", bound="ConnectionSettingsBase")

_KNOWN_KWARGS_CACHE: dict[type[ConnectionSettingsBase], dict[str, bool]] = {}


@dataclass(frozen=True)
class ConnectionSettingsBase(_Configurable):
    """Provider-independent settings constructed directly or with ``from_config``.

    Binding accepts a scoped mapping/Configuration, or a connection definition
    with a literal ``settings`` child. It does not search an application root.
    Use canonical field names for exact lookups; individual provider binders
    explicitly opt into legacy case/underscore matching where supported.
    Unrecognized keys are retained in ``extras``; an explicit ``extras`` mapping
    overrides matching unrecognized keys.

    An already-bound instance is reused by ``from_config``. ``None`` binds
    defaults. Legacy AgentAuthConfiguration conversion is a separate internal
    compatibility path.
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
        attrs = dict(vars(agent_auth_config))
        attrs.pop("_connections", None)
        attrs.pop("_configured_issuers", None)
        attrs.update(attrs.pop("provider_settings", {}))
        attrs["ISSUERS"] = agent_auth_config.ISSUERS
        return cls.from_config(attrs)

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        return {
            "client_id": config.get_strn(legpath("client_id")),
            "authority": config.get_strn(netpath("authority"))
            or config.get_strn(netpath("authorityendpoint")),
            "tenant_id": config.get_strn(legpath("tenant_id")),
            "scopes": config.get_scopes(netpath("scopes")),
            "alternate_blueprint_connection_name": config.get_strn(
                legpath("alt_blueprint_name")
            )
            or config.get_strn(legpath("alternate_blueprint_connection_name")),
        }

    @classmethod
    def _known_kwargs(cls) -> dict[str, bool]:

        if cls in _KNOWN_KWARGS_CACHE:
            return _KNOWN_KWARGS_CACHE[cls]

        base = [f.name for f in fields(cls) if f.init and f.name != "_extras"]
        final = {}
        for n in base:
            final[n] = True

        _KNOWN_KWARGS_CACHE[cls] = final
        return final

    @classmethod
    def _get_extras(cls, config: Configuration) -> Configuration:
        known_kwargs = cls._known_kwargs()
        base = {}
        for k, v in config.items():
            if not _get_bool(known_kwargs, legpath(k), default=False):
                base[k] = v
        extras = _pop(base, "extras", default={})
        base = {**base, **extras}
        return Configuration.from_config(base, _base_path=config._base_path)

    @classmethod
    def _from_config(cls, config: Configuration) -> Self:
        try:
            settings = config.get_section(netpath("settings"))
        except KeyError:
            settings = config
        return cls(**cls._get_init_kwargs(settings), _extras=cls._get_extras(settings))

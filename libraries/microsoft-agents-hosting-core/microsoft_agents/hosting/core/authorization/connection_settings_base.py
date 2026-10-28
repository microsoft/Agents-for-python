# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Any, TYPE_CHECKING
from typing_extensions import Self

from microsoft_agents.activity.config import Configuration, _Configurable, xpath

if TYPE_CHECKING:
    from .agent_auth_configuration import AgentAuthConfiguration


def _read(configuration: Any, *names: str, default: Any = None) -> Any:
    """Read the first populated attribute from ``configuration``.

    Tolerates both the SDK's upper-case configuration keys (e.g. ``CLIENT_ID``)
    and the snake_case property aliases, so settings can be bound from an
    :class:`AgentAuthConfiguration`, a raw mapping-like object, or another
    settings instance.
    """
    is_mapping = isinstance(configuration, Mapping)
    for name in names:
        value = (
            configuration.get(name)
            if is_mapping
            else getattr(configuration, name, None)
        )
        if value is not None:
            return value
    return default


class _ConnectionSettingsBase:
    """Common, provider-agnostic connection settings shared by all providers.

    Mirrors the .NET ``Microsoft.Agents.Authentication.ConnectionSettingsBase``
    abstract base. Provider-specific settings classes (for example the Entra
    sidecar's :class:`SidecarConnectionSettings`) extend this with their own
    fields, enabling an extensible, connection-type-based configuration model
    that matches the .NET provider pattern.

    Instances are normally produced from an :class:`AgentAuthConfiguration`
    (the raw, provider-agnostic configuration bag) via
    :meth:`from_configuration`. Subclasses bind their own fields and merge the
    common base fields via :meth:`base_kwargs_from_configuration`.

    Property names are the Python snake_case equivalents of the .NET
    ``ConnectionSettingsBase`` properties:

    ====================================  ====================================
    .NET                                  Python
    ====================================  ====================================
    ``ClientId``                          ``client_id``
    ``AuthorityEndpoint``                 ``authority``
    ``TenantId``                          ``tenant_id``
    ``Scopes``                            ``scopes``
    ``AlternateBlueprintConnectionName``  ``alternate_blueprint_connection_name``
    ====================================  ====================================
    """

    def __init__(
        self,
        *,
        client_id: str | None = None,
        authority: str | None = None,
        tenant_id: str | None = None,
        scopes: list[str] | None = None,
        alternate_blueprint_connection_name: str | None = None,
    ):
        self.client_id = client_id
        self.authority = authority
        self.tenant_id = tenant_id
        self.scopes = scopes
        self.alternate_blueprint_connection_name = alternate_blueprint_connection_name

    @staticmethod
    def base_kwargs_from_configuration(
        configuration: "AgentAuthConfiguration",
    ) -> dict:
        """Bind the common base fields from an :class:`AgentAuthConfiguration`.

        Returns a kwargs dict suitable for passing to ``__init__``. Subclasses
        call this and merge it with their own provider-specific kwargs so the
        base fields stay defined in a single place.
        """
        # Accept both the underscored configuration keys and the SDK's env-style
        # keys (e.g. ``load_configuration_from_env`` yields ``CLIENTID`` /
        # ``TENANTID`` without underscores) so binding from a raw ``SETTINGS``
        # mapping doesn't silently drop values.
        return dict(
            client_id=_read(configuration, "CLIENT_ID", "CLIENTID", "client_id"),
            authority=_read(
                configuration, "AUTHORITY", "AUTHORITYENDPOINT", "authority"
            ),
            tenant_id=_read(configuration, "TENANT_ID", "TENANTID", "tenant_id"),
            scopes=_read(configuration, "SCOPES", "scopes"),
            alternate_blueprint_connection_name=_read(
                configuration,
                "ALT_BLUEPRINT_ID",
                "ALT_BLUEPRINT_NAME",
                "ALTERNATEBLUEPRINTCONNECTIONNAME",
                "alternate_blueprint_connection_name",
            ),
        )

    @classmethod
    def from_configuration(
        cls, configuration: "AgentAuthConfiguration"
    ) -> "_ConnectionSettingsBase":
        """Build base settings from an :class:`AgentAuthConfiguration`."""
        return cls(**cls.base_kwargs_from_configuration(configuration))


_KNOWN_KWARGS_CACHE: dict[type[ConnectionSettingsBase], list[str]] = {}


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
        attrs = dict(vars(agent_auth_config))
        attrs.update(attrs.pop("provider_settings", {}))
        attrs["ISSUERS"] = agent_auth_config.ISSUERS
        return cls.from_mapping(attrs)

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        return {
            "client_id": config.get_strn(cls._xpath("client_id")),
            "authority": config.get_strn(
                cls._xpath("authority"), cls._xpath("authorityendpoint")
            ),
            "tenant_id": config.get_strn(cls._xpath("tenant_id")),
            "scopes": config.get_scopes(cls._xpath("scopes")),
            "alternate_blueprint_connection_name": config.get_strn(
                "alt_blueprint_name",
                "ALT_BLUEPRINT_NAME",
                "alt_blueprint_id",
                "ALT_BLUEPRINT_ID",
                *cls._xpath("alternate_blueprint_connection_name"),
            ),
        }

    @classmethod
    def _known_kwargs(cls) -> list[str]:
        if cls not in _KNOWN_KWARGS_CACHE:
            _KNOWN_KWARGS_CACHE[cls] = [
                alias
                for f in fields(cls)
                if f.init and f.name != "_extras"
                for alias in xpath(f.name)
            ]
        return _KNOWN_KWARGS_CACHE[cls]

    @classmethod
    def _get_extras(cls, config: Configuration) -> Configuration:
        known_kwargs = cls._known_kwargs()
        base = {k: v for k, v in config.items() if k not in known_kwargs}
        return Configuration.from_mapping(
            base, _base_path=config._base_path, **base.pop("extras", {})
        )

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

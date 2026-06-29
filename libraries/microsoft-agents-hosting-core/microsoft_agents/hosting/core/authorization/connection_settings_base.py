# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TYPE_CHECKING

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


class ConnectionSettingsBase:
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
    ) -> "ConnectionSettingsBase":
        """Build base settings from an :class:`AgentAuthConfiguration`."""
        return cls(**cls.base_kwargs_from_configuration(configuration))

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from microsoft_agents.activity.config import (
    Configuration,
    _Configurable,
    _legpath as legpath,
    _netpath as netpath,
)
from microsoft_agents.activity.config._metadata import _RootConfigMetadata

from .jwt_connection_settings import JwtConnectionSettings


@dataclass(frozen=True)
class TokenValidationConfiguration(_Configurable):
    """Settings that determine which incoming access tokens the agent accepts.

    ``audiences`` lists the client IDs that a token may be intended for.
    ``anonymous_allowed`` controls whether requests without authentication are
    allowed.

    To read the full application's settings, first use
    ``load_configuration_from_env``. ``from_config`` then reads
    ``token_validation`` and ``connections`` automatically. If no nonempty
    audience list is provided, the configured connection client IDs are used::

        >>> from microsoft_agents.activity.config import load_configuration_from_env
        >>> from microsoft_agents.hosting.core.authorization.jwt import (
        ...     TokenValidationConfiguration,
        ... )
        >>> config = load_configuration_from_env({
        ...     "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENT_ID": "your-client-id",
        ...     "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANT_ID": "your-tenant-id",
        ... })
        >>> policy = TokenValidationConfiguration.from_config(config)
        >>> policy.audiences
        ['your-client-id']
        >>> policy.tenant_id
        'your-tenant-id'

    The tenant ID and anonymous-access option also fall back to
    ``SERVICE_CONNECTION`` when not set in ``token_validation``.
    An explicit ``anonymous_allowed=False`` always disables anonymous access.

    To supply just the token-validation options, pass those fields directly::

        >>> policy = TokenValidationConfiguration.from_config({
        ...     "audiences": ["your-client-id"],
        ...     "anonymous_allowed": False,
        ... })
        >>> policy.validate_audience("your-client-id")
        True

    A plain dictionary is read as these fields, not searched for nested
    application sections. It does not supply connection details for checking
    token signatures. For programmatic setup that also needs those details,
    pass ``connections`` or ``default_jwt_settings`` to the constructor.
    Passing an existing instance to ``from_config`` returns it unchanged.
    """

    tenant_id: str | None = None
    audiences: list[str] = field(default_factory=list)
    anonymous_allowed: bool = False
    default_jwt_settings: JwtConnectionSettings | None = None
    connections: dict[str, JwtConnectionSettings] = field(default_factory=dict)

    @classmethod
    def _from_config(cls, configuration: Configuration) -> TokenValidationConfiguration:

        token_validation: Configuration = configuration
        connection_raw_items = {}

        if _RootConfigMetadata.get(configuration):
            token_validation = configuration.get_section(
                legpath("token_validation"), default=Configuration()
            )
            connection_raw_items = configuration.get_items(netpath("connections"))

        audiences = token_validation.get_str_list(netpath("audiences"))
        tenant_id = token_validation.get_strn(legpath("tenant_id"))
        anonymous_allowed = token_validation.get_booln(legpath("anonymous_allowed"))

        connections: dict[str, JwtConnectionSettings] = {}
        for name, conf in connection_raw_items:
            connections[name] = JwtConnectionSettings.from_config(conf)

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
        """Return whether a token's audience is in the accepted client ID list.

        Comparison ignores case. Empty or non-string values are not accepted.
        """
        if not aud or not isinstance(aud, str):
            return False
        for target_audience in self.audiences:
            if aud.lower() == target_audience.lower():
                return True
        return False

    def get_connection_settings(self, aud: Any) -> JwtConnectionSettings | None:
        """Find the connection whose client ID matches a token's audience.

        If no client ID matches, return ``default_jwt_settings``. Empty or
        non-string audiences return ``None``. This only selects settings;
        call ``validate_audience`` to check whether the audience is allowed.
        """
        if not aud or not isinstance(aud, str):
            return None
        for conn in self.connections.values():
            if conn.client_id and conn.client_id.lower() == aud.lower():
                return conn
        return self.default_jwt_settings

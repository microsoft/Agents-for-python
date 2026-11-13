"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import logging
import warnings

from dataclasses import dataclass, field

from microsoft_agents.activity.config import (
    _Configurable,
    Configuration,
    _legpath as legpath,
)

logger = logging.getLogger(__name__)


def _or_default(s: str | None, default: str) -> str:
    return (s.strip() if s else None) or default


def _create_kwargs(
    name: str | None = None,
    title: str | None = None,
    text: str | None = None,
    abs_oauth_connection_name: str | None = None,
    obo_connection_name: str | None = None,
    auth_type: str | None = None,
    scopes: list[str] | None = None,
    _alt_blueprint_name: str | None = None,
    **kwargs,
) -> dict:
    c = Configuration(kwargs)
    return dict(
        name=_or_default(name, c.get_str(legpath("name"), default="")),
        title=_or_default(title, c.get_str(legpath("title"), default="")),
        text=_or_default(text, c.get_str(legpath("text"), default="")),
        abs_oauth_connection_name=_or_default(
            abs_oauth_connection_name,
            c.get_str(legpath("azurebotoauthconnectionname"), default=""),
        ),
        obo_connection_name=_or_default(
            obo_connection_name, c.get_str(legpath("oboconnectionname"), default="")
        ),
        auth_type=_or_default(
            auth_type, c.get_str(legpath("type"), default="UserAuthorization")
        ).lower(),
        scopes=Configuration.format_scopes(scopes or c.get(legpath("scopes"))),
        _alt_blueprint_name=_alt_blueprint_name
        or c.get_strn(legpath("alt_blueprint_name")),
    )


@dataclass
class AuthHandlerConfig(_Configurable):
    """Settings for one named sign-in option, such as access to Microsoft Graph.

    Create with keyword arguments, or use ``from_config`` to read a settings
    dictionary. The latter also accepts configuration names such as
    ``AZUREBOTOAUTHCONNECTIONNAME`` and converts scope text to a list::

        >>> from microsoft_agents.hosting.core import AuthHandlerConfig
        >>> handler = AuthHandlerConfig.from_config({
        ...     "name": "graph",
        ...     "AZUREBOTOAUTHCONNECTIONNAME": "graph-oauth",
        ...     "scopes": "User.Read, Mail.Read",
        ... })
        >>> handler.abs_oauth_connection_name
        'graph-oauth'
        >>> handler.scopes
        ['User.Read', 'Mail.Read']

    When using constructor arguments instead, pass ``scopes`` as a list.
    ``from_config`` also converts the authorization type to lowercase.

    :param name: Handler identifier; use the corresponding handlers-mapping key.
    :param title: Sign-in card title.
    :param text: Sign-in card text.
    :param abs_oauth_connection_name: Azure Bot OAuth connection name.
    :param obo_connection_name: SDK connection used for on-behalf-of exchange.
    :param auth_type: UserAuthorization, AgenticUserAuthorization, or
        ConnectorUserAuthorization. Authorization selects these case-insensitively.
    :param scopes: Default scopes for token acquisition or exchange.
    :param _alt_blueprint_name: Optional alternate connection for agentic user
        token acquisition.
    """

    name: str = ""
    title: str = ""
    text: str = ""
    abs_oauth_connection_name: str = ""
    obo_connection_name: str = ""
    auth_type: str = "userauthorization"
    scopes: list[str] = field(default_factory=list)
    _alt_blueprint_name: str | None = None

    @classmethod
    def _from_config(cls, config: Configuration) -> AuthHandlerConfig:
        return AuthHandlerConfig(**_create_kwargs(**config))

    @staticmethod
    def _format_scopes(scopes: str | list[str]) -> list[str]:
        if isinstance(scopes, str):
            lst = scopes.strip().split(" ")
        else:
            lst = scopes
        return [s for s in lst if s]


class AuthHandler(AuthHandlerConfig):
    """Deprecated compatibility constructor for AuthHandlerConfig.

    Accepts legacy positional fields and configuration keyword aliases, and
    emits a DeprecationWarning. Use AuthHandlerConfig for typed construction
    or ``AuthHandlerConfig.from_config`` for configuration binding.
    """

    def __init__(self, *args, **kwargs):
        """Bind legacy arguments and emit the constructor deprecation warning."""

        warnings.warn(
            "AuthHandler is deprecated. Please use AuthHandlerConfig instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**_create_kwargs(*args, **kwargs))

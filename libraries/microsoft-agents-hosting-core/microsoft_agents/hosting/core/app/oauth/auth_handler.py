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
    xpath,
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
        name=_or_default(name, c.get_str(xpath("name"), default="")),
        title=_or_default(title, c.get_str(xpath("title"), default="")),
        text=_or_default(text, c.get_str(xpath("text"), default="")),
        abs_oauth_connection_name=_or_default(
            abs_oauth_connection_name,
            c.get_str(xpath("azurebotoauthconnectionname"), default=""),
        ),
        obo_connection_name=_or_default(
            obo_connection_name, c.get_str(xpath("oboconnectionname"), default="")
        ),
        auth_type=_or_default(
            auth_type, c.get_str(xpath("type"), default="UserAuthorization")
        ).lower(),
        scopes=Configuration.format_scopes(scopes or c.get(xpath("scopes"))),
        _alt_blueprint_name=_alt_blueprint_name
        or c.get_strn(xpath("alt_blueprint_name")),
    )


@dataclass
class AuthHandlerSettings(_Configurable):
    """
    Interface defining an authorization handler for OAuth flows.
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
    def _from_configuration(cls, config: Configuration) -> AuthHandlerSettings:
        return AuthHandlerSettings(**_create_kwargs(**config))

    @staticmethod
    def _format_scopes(scopes: str | list[str]) -> list[str]:
        if isinstance(scopes, str):
            lst = scopes.strip().split(" ")
        else:
            lst = scopes
        return [s for s in lst if s]


class AuthHandler(AuthHandlerSettings):
    """Deprecated. Use AuthHandlerSettings instead."""

    def __init__(self, *args, **kwargs):
        """Initialize the deprecated AuthHandler class."""

        warnings.warn(
            "AuthHandler is deprecated. Please use AuthHandlerSettings instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**_create_kwargs(*args, **kwargs))

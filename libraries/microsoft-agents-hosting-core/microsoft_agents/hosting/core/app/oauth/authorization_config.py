"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from microsoft_agents.activity.config import (
    Configuration,
    _RootConfigurable,
    _legpath as legpath,
    _get,
    _get_str,
)
from .auth_handler import AuthHandlerConfig


@dataclass(frozen=True)
class AuthorizationConfig(_RootConfigurable):
    """Choose the agent's sign-in options and named OAuth handlers.

    Each handler describes one way users can sign in. To read only these
    options, pass a dictionary with ``auto_sign_in`` and ``handlers``::

        >>> from microsoft_agents.hosting.core import AuthorizationConfig
        >>> options = AuthorizationConfig.from_config({
        ...     "auto_sign_in": True,
        ...     "handlers": {
        ...         "graph": {
        ...             "type": "UserAuthorization",
        ...             "settings": {
        ...                 "AZUREBOTOAUTHCONNECTIONNAME": "graph-oauth",
        ...                 "scopes": "User.Read",
        ...             },
        ...         },
        ...     },
        ... })
        >>> options.auto_sign_in
        True
        >>> options.handlers["graph"].abs_oauth_connection_name
        'graph-oauth'

    For full application configuration returned by
    ``load_configuration_from_env``, these options are read from
    ``agent_application`` > ``user_authorization`` automatically.
    If the section is missing, there are no handlers and automatic sign-in is
    disabled.

    In a handler dictionary, ``type`` selects the authorization flow and
    ``settings`` contains its options. If ``type`` is absent, a nested
    ``auth_type`` is used instead. The dictionary key, such as ``"graph"``,
    supplies the handler name even if a different name appears in its settings.

    You can also construct AuthorizationConfig directly with AuthHandlerConfig
    objects. Names such as ``AUTO_SIGN_IN`` and ``auto_sign_in`` are equivalent.

    :param auto_sign_in: Whether to attempt sign-in automatically before routes.
    :param handlers: Dictionary of handler IDs and AuthHandlerConfig objects.
    """

    auto_sign_in: bool = False
    handlers: dict[str, AuthHandlerConfig] = field(default_factory=dict)

    @classmethod
    def _from_scoped_configuration(cls, config: Configuration) -> AuthorizationConfig:
        handlers_config = config.get(legpath("handlers"), default={})
        handlers = {}
        for handler_name, subconfig in handlers_config.items():
            extra = dict(_get(subconfig, legpath("settings"), default={}))
            if "name" in extra:
                del extra["name"]
            handler_type = _get_str(subconfig, legpath("type"), default="")
            if "auth_type" in extra:
                nested_type = extra.pop("auth_type")
                handler_type = handler_type or nested_type
            handlers[handler_name] = AuthHandlerConfig.from_config(
                dict(name=handler_name, auth_type=handler_type, **extra)
            )
        return AuthorizationConfig(
            auto_sign_in=config.get_bool(legpath("auto_sign_in"), default=False),
            handlers=handlers,
        )

    @classmethod
    def _from_root_configuration(cls, config: Configuration) -> AuthorizationConfig:
        return cls._from_scoped_configuration(
            config.get_section(
                legpath("agent_application", "user_authorization"),
                default=Configuration(),
            )
        )

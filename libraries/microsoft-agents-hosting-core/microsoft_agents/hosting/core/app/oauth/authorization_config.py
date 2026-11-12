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
    """Application-level OAuth options and named handler definitions.

    Root configuration traverses ``agent_application`` / ``user_authorization``. Scoped
    configuration reads ``auto_sign_in`` and ``handlers`` directly. A missing
    section binds the defaults: no handlers and automatic sign-in disabled.

    Construct this dataclass directly with AuthHandlerConfig values, or bind
    a mapping or Configuration with ``from_config``. In mapped
    configuration, each handler has a ``settings`` mapping and an optional
    ``type`` at handler level. A nested ``auth_type`` is used when the outer
    type is absent. The handler key supplies its name, overriding a nested name.
    Automatic sign-in and handler-section names ignore case and underscores.

    :param auto_sign_in: Whether to attempt sign-in automatically before routes.
    :param handlers: Handler IDs mapped to bound AuthHandlerConfig instances.
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

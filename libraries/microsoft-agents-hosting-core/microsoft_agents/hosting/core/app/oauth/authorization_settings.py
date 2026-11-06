"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from microsoft_agents.activity.config import (
    Configuration,
    _RootConfigurable,
    xpath,
    _get,
    _get_str,
)
from .auth_handler import AuthHandlerSettings


@dataclass(frozen=True)
class AuthorizationSettings(_RootConfigurable):
    """Application-level OAuth options and named handler definitions.

    Root configuration reads ``agent_application::user_authorization``. Scoped
    configuration reads ``auto_sign_in`` and ``handlers`` directly. A missing
    section binds the defaults: no handlers and automatic sign-in disabled.

    Construct this dataclass directly with AuthHandlerSettings values, or bind
    configuration with ``from_mapping`` / ``from_configuration``. In mapped
    configuration, each handler has a ``settings`` mapping and an optional
    ``type`` at handler level or inside ``settings``. The handler key supplies
    its name.

    :param auto_sign_in: Whether to attempt sign-in automatically before routes.
    :param handlers: Handler IDs mapped to bound AuthHandlerSettings instances.
    """

    auto_sign_in: bool = False
    handlers: dict[str, AuthHandlerSettings] = field(default_factory=dict)

    @classmethod
    def _from_scoped_configuration(cls, config: Configuration) -> AuthorizationSettings:
        handlers_config = config.get(xpath("handlers"), default={})
        handlers = {}
        for handler_name, subconfig in handlers_config.items():
            extra = dict(_get(subconfig, *xpath("settings"), default={}))
            if "name" in extra:
                del extra["name"]
            handler_type = _get_str(subconfig, *xpath("type"), default="")
            if "auth_type" in extra:
                nested_type = extra.pop("auth_type")
                handler_type = handler_type or nested_type
            handlers[handler_name] = AuthHandlerSettings.from_mapping(
                dict(name=handler_name, auth_type=handler_type, **extra)
            )
        return AuthorizationSettings(
            auto_sign_in=config.get_bool(xpath("auto_sign_in"), default=False),
            handlers=handlers,
        )

    @classmethod
    def _from_root_configuration(cls, config: Configuration) -> AuthorizationSettings:
        return cls._from_scoped_configuration(
            config.get_section(
                xpath("agent_application", "user_authorization"),
                default=Configuration(),
            )
        )

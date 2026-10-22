# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field

from microsoft_agents.activity.config import Configuration, xpath

from ..connections import ConnectionSettingsBase

@dataclass(frozen=True)
class JwtConnectionSettings(ConnectionSettingsBase):
    """
    Connection settings for MSAL authentication.
    """

    validate_issuer: bool = False
    issuers: list[str] = field(default_factory=list)
    anonymous_allowed: bool = False

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        base = super()._get_init_kwargs(config)        
        base.update({
            "validate_issuer": config.get_bool(xpath("validate_issuer"), default=False),
            "issuers": config.get_str_list(xpath("issuers")),
            "anonymous_allowed": config.get_bool(xpath("anonymous_allowed"), default=False)
        })
        return base
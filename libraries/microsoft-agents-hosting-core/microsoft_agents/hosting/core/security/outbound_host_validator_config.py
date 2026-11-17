# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from typing import Self

from microsoft_agents.activity.config import (
    Configuration,
    _RootConfigurable,
    _netpath,
)


@dataclass(frozen=True)
class OutboundHostValidatorConfig(_RootConfigurable):

    enabled: bool = False
    include_default_microsoft_hosts: bool = True
    allow_private_network_addresses: bool = False
    allow_http_for_loopback: bool = False
    hosts: list[str] = field(default_factory=list)

    @classmethod
    def _from_scoped_configuration(cls, config: Configuration) -> Self:
        return cls(
            enabled=config.get_bool(_netpath("Enabled"), False),
            include_default_microsoft_hosts=config.get_bool(
                _netpath("IncludeDefaultMicrosoftHosts"), True
            ),
            allow_private_network_addresses=config.get_bool(
                _netpath("AllowPrivateNetworkAddresses"), False
            ),
            allow_http_for_loopback=config.get_bool(
                _netpath("AllowHttpForLoopback"), False
            ),
            hosts=config.get_str_list(_netpath("Hosts")),
        )

    @classmethod
    def _from_root_configuration(cls, config: Configuration) -> Self:
        return cls._from_scoped_configuration(
            config.get_section(
                _netpath("OutboundHostValidator"), default=Configuration()
            )
        )

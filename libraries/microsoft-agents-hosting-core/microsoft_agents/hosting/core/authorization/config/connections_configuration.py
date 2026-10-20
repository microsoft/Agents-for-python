# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from typing import Mapping
from typing_extensions import Self

from microsoft_agents.activity.config import Configuration, _Configurable

@dataclass(frozen=True)
class _ConnectionSettingsBase(_Configurable):

    client_id: str = ""
    authority: str = ""
    tenant_id: str = ""
    scopes: list[str] = field(default_factory=list)
    alternate_blueprint_connection_name: str = ""

    @classmethod
    def from_configuration(self, config: Configuration) -> Self:
        return self(
            client_id=config.get_value(str, "client_id", None)
            authority=config.get_value(str, "authority", None)
            tenant_id=config.get_value(str, "tenant_id", None)
            scopes=config.get_value(list[str], "scopes", None)
            alternate_blueprint_connection_name=config.get_typed(str, "alternate_blueprint_connection_name", default="")
        )
        


class _ConnectionsConfiguration:


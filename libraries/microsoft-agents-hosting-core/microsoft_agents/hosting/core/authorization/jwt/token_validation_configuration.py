# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any

from microsoft_agents.activity.config import Configuration, _Configurable, _utils, xpath
from ..connections import ConnectionSettingsBase

class TokenValidationConfiguration(_Configurable):

    def __init__(self, configuration: Configuration):
        self._configuration = configuration

        token_validation = configuration.get_section("token_validation")
        self._audiences = token_validation.collect_str("audience", "AUDIENCES")
        self._tenant_id = token_validation.get_str(*xcase("tenant_id"), default="")

        if not self._audiences:
            

            self._audiences = configuration.collect_str(
                *xpath("connections", "*", "settings", "client_id")
            )

            
        if not self._audiences or not self._tenant_id: # get the default audiences from the connections

            connections = configuration.get_sections(*xpath()
            for conn_name, conn_obj in connections.items():
                
                settings = Configuration.from_mapping(conn_obj.get("settings", {}))

                if conn_name.upper() == "SERVICE_CONNECTION":
                    tenant_id =settings.get_

            for item in configuration.collect("connections")

            update_audiences = not self._audiences
            update_tenant_id = not self._tenant_id

            ConnectionSettingsBase.from_configuration(configuration)

            sections = configuration.get_sections(*xpath("connections", "*", "settings"))
            for sub in sections:
                if update_audiences:
                    aud = sub.get_strn(*xpath("client_id"))
                    if aud:
                        self._audiences.append(aud)

                if "SERIVCE_CONNECTION" in sub._base_path




            update_audiences = not self._audiences
            update_tenant_id = not self._tenant_id

            connections = configuration.get("connections", {})
            for conn_obj in connections.values():
                aud = _utils._get(
                    conn_obj, 
                    *xpath("settings", "client_id"),
                    default=None
                )
                if update_audiences and aud:
                    self._audiences.append(aud)
                    if update_tenant_id:
                        self._tenant_id = aud
        
            


    @classmethod
    def _from_configuration(cls, configuration: Configuration) -> TokenValidationConfiguration:
        return TokenValidationConfiguration(configuration)

    def _is_valid_aud(self, aud: Any) -> bool:
        if not isinstance(aud, str):
            return False
        for conn in self._connections.values():
            if not conn.CLIENT_ID:
                continue
            if aud.lower() == conn.CLIENT_ID.lower():
                return True
        return False

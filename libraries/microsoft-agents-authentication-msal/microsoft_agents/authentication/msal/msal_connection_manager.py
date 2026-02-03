# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
from typing import Dict, List, Optional
from collections.abc import Iterator
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AccessTokenProviderBase,
    ClaimsIdentity,
    Connections,
)

from .msal_auth import MsalAuth


class MsalConnectionManager(Connections):
    _connections: Dict[str, MsalAuth]
    _connections_map: List[Dict[str, str]]
    _service_connection_configuration: AgentAuthConfiguration

    def __init__(
        self,
        connections_configurations: Optional[Dict[str, AgentAuthConfiguration]] = None,
        connections_map: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ):
        """
        Initialize the MSAL connection manager.

        :arg connections_configurations: A dictionary of connection configurations.
        :type connections_configurations: Dict[str, :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`]
        :arg connections_map: A list of connection mappings.
        :type connections_map: List[Dict[str, str]]
        :raises ValueError: If no service connection configuration is provided.
        """

        self._connections: Dict[str, MsalAuth] = {}
        self._connections_map = connections_map or kwargs.get("CONNECTIONSMAP", {})
        self._config_map: dict[str, AgentAuthConfiguration] = {}

        if connections_configurations:
            for (
                connection_name,
                agent_auth_config,
            ) in connections_configurations.items():
                self._connections[connection_name] = MsalAuth(agent_auth_config)
                self._config_map[connection_name] = agent_auth_config
        else:
            raw_configurations: Dict[str, Dict] = kwargs.get("CONNECTIONS", {})
            for connection_name, connection_settings in raw_configurations.items():
                parsed_configuration = AgentAuthConfiguration(
                    **connection_settings.get("SETTINGS", {})
                )
                self._connections[connection_name] = MsalAuth(parsed_configuration)
                self._config_map[connection_name] = parsed_configuration

        # JWT-patch
        for connection_name, config in self._config_map.items():
            config._connections = self._config_map

        if not self._connections.get("SERVICE_CONNECTION", None):
            raise ValueError("No service connection configuration provided.")

    def get_connection(self, connection_name: Optional[str]) -> AccessTokenProviderBase:
        """
        Get the OAuth connection for the agent.

        :arg connection_name: The name of the connection.
        :type connection_name: Optional[str]
        :return: The OAuth connection for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AccessTokenProviderBase`
        """
        connection_name = connection_name or "SERVICE_CONNECTION"
        connection = self._connections.get(connection_name, None)
        if not connection:
            raise ValueError(f"No connection found for '{connection_name}'.")
        return connection

    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default OAuth connection for the agent.

        :return: The default OAuth connection for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AccessTokenProviderBase`
        """
        connection = self._connections.get("SERVICE_CONNECTION", None)
        if not connection:
            raise ValueError(
                "No default service connection found. Expected 'SERVICE_CONNECTION'."
            )
        return connection

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent.

        :arg claims_identity: The claims identity of the bot.
        :type claims_identity: :class:`microsoft_agents.hosting.core.ClaimsIdentity`
        :arg service_url: The service URL of the bot.
        :type service_url: str
        :return: The OAuth token provider for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AccessTokenProviderBase`
        :raises ValueError: If no connection is found for the given audience and service URL.
        """
        if not claims_identity or not service_url:
            raise ValueError(
                "Claims identity and Service URL are required to get the token provider."
            )

        if not self._connections_map:
            return self.get_default_connection()

        aud = claims_identity.get_app_id() or ""
        for item in self._connections_map:
            audience_match = True
            item_aud = item.get("AUDIENCE", "")
            if item_aud:
                audience_match = item_aud.lower() == aud.lower()

            if audience_match:
                item_service_url = item.get("SERVICEURL", "")
                if item_service_url == "*" or item_service_url == "":
                    connection_name = item.get("CONNECTION")
                    connection = self.get_connection(connection_name)
                    if connection:
                        return connection

                else:
                    res = re.match(item_service_url, service_url, re.IGNORECASE)
                    if res:
                        connection_name = item.get("CONNECTION")
                        connection = self.get_connection(connection_name)
                        if connection:
                            return connection

        raise ValueError(
            f"No connection found for audience '{aud}' and serviceUrl '{service_url}'."
        )

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        """
        Get the default connection configuration for the agent.

        :return: The default connection configuration for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`
        """
        config = self._config_map.get("SERVICE_CONNECTION")
        if not config:
            raise ValueError(
                "No default service connection configuration found. Expected 'SERVICE_CONNECTION'."
            )
        return config

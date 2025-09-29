import re
from typing import Dict, List, Optional
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AccessTokenProviderBase,
    ClaimsIdentity,
    Connections,
)

from .msal_auth import MsalAuth


class MsalConnectionManager(Connections):
    def __init__(
        self,
        connections_configurations: Dict[str, AgentAuthConfiguration] = None,
        connections_map: List[Dict[str, str]] = None,
        **kwargs
    ):
        self._connections: Dict[str, MsalAuth] = {}
        self._connections_map = connections_map or kwargs.get("CONNECTIONSMAP", {})
        self._service_connection_configuration: AgentAuthConfiguration = None

        if connections_configurations:
            for (
                connection_name,
                connection_settings,
            ) in connections_configurations.items():
                self._connections[connection_name] = MsalAuth(
                    AgentAuthConfiguration(**connection_settings)
                )
        else:
            raw_configurations: Dict[str, Dict] = kwargs.get("CONNECTIONS", {})
            for connection_name, connection_settings in raw_configurations.items():
                parsed_configuration = AgentAuthConfiguration(
                    **connection_settings.get("SETTINGS", {})
                )
                self._connections[connection_name] = MsalAuth(parsed_configuration)
                if connection_name == "SERVICE_CONNECTION":
                    self._service_connection_configuration = parsed_configuration

        if not self._connections.get("SERVICE_CONNECTION", None):
            raise ValueError("No service connection configuration provided.")

    def get_connection(self, connection_name: Optional[str]) -> AccessTokenProviderBase:
        """
        Get the OAuth connection for the agent.
        """
        return self._connections.get(connection_name, None)

    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default OAuth connection for the agent.
        """
        return self._connections.get("SERVICE_CONNECTION", None)

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent.
        """
        if not claims_identity or not service_url:
            raise ValueError("Claims identity and Service URL are required to get the token provider.")    

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
        """
        return self._service_connection_configuration

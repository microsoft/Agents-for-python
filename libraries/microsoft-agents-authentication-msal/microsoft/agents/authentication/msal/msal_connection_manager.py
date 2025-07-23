from typing import Dict, List, Optional
from microsoft.agents.hosting.core.authorization import (
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
        self._connections_map = connections_map or kwargs.get("CONNECTIONS_MAP", {})
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
        if not self._connections_map:
            return self.get_default_connection()

        # TODO: Implement logic to select the appropriate connection based on the connection map

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        """
        Get the default connection configuration for the agent.
        """
        return self._service_connection_configuration

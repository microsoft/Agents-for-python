from typing import Dict, List, Optional
from microsoft.agents.authorization import (
    AgentAuthConfiguration,
    AccessTokenProviderBase,
    ClaimsIdentity,
    Connections,
)

from .msal_auth import MsalAuth


class MsalConnectionManager(Connections):

    def __init__(
        self,
        connections: Dict[str, AgentAuthConfiguration] = None,
        connections_map=List[Dict[str, str]],
        **kwargs
    ):
        self._connections = connections
        self._connections_map = connections_map or kwargs.get("CONNECTIONS_MAP", None)
        if not self._connections:
            connections_configs: Dict[str, Dict] = kwargs.get("CONNECTIONS", {})
            for connection_name, connection_settings in connections_configs.items():
                self._connections[connection_name] = MsalAuth(
                    AgentAuthConfiguration(**connection_settings.get("SETTINGS", None))
                )
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

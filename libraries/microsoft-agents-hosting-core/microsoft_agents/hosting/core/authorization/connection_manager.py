# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
import logging

from collections.abc import Callable

from microsoft_agents.activity import (
    Activity,
    RoleTypes
)

from .agent_auth_configuration import AgentAuthConfiguration
from .access_token_provider_base import AccessTokenProviderBase
from .claims_identity import ClaimsIdentity
from .connections import Connections

from ._log_config import _log_config

logger = logging.getLogger(__name__)


class ConnectionManager(Connections):
    """
    Generic, provider-agnostic connection manager.

    Dispatches to any :class:`AccessTokenProviderBase` implementation. The
    ``provider_factory`` callable determines which auth provider is instantiated
    for each connection configuration, so new auth providers (MSAL, Entra ID
    sidecar, future providers) can reuse the connection routing logic without
    duplicating it.
    """

    _connections: dict[str, AccessTokenProviderBase]
    _connections_map: list[dict[str, str]]
    _config_map: dict[str, AgentAuthConfiguration]

    def __init__(
        self,
        provider_factory: Callable[[AgentAuthConfiguration], AccessTokenProviderBase],
        connections_configurations: dict[str, AgentAuthConfiguration] | None = None,
        connections_map: list[dict[str, str]] | None = None,
        **kwargs,
    ):
        """
        Initialize the connection manager.

        :param provider_factory: Factory that creates an
            :class:`microsoft_agents.hosting.core.AccessTokenProviderBase` from an
            :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`.
        :type provider_factory: Callable[[AgentAuthConfiguration], AccessTokenProviderBase]
        :param connections_configurations: A dictionary of connection configurations.
        :type connections_configurations: dict[str, :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`]
        :param connections_map: A list of connection mappings.
        :type connections_map: list[dict[str, str]]
        :raises ValueError: If no service connection configuration is provided.
        """

        self._provider_factory = provider_factory
        self._connections = {}
        # ``load_configuration_from_env`` yields CONNECTIONSMAP as a list when it
        # is configured (it collapses the parsed name->entry dict to a list) and
        # as an empty dict ({}) only when unset. Normalize to a list so the guard
        # also handles a raw dict passed via direct/manual construction and the
        # empty-unset case, keeping the runtime shape consistent with the
        # list[dict[str, str]] the class expects everywhere else.
        raw_connections_map = (
            connections_map
            if connections_map is not None
            else kwargs.get("CONNECTIONSMAP", [])
        )

        if isinstance(raw_connections_map, dict):
            raw_connections_map = list(raw_connections_map.values())
        self._connections_map = raw_connections_map or []
        self._config_map = {}

        if connections_configurations:
            for (
                connection_name,
                agent_auth_config,
            ) in connections_configurations.items():
                self._connections[connection_name] = provider_factory(agent_auth_config)
                self._config_map[connection_name] = agent_auth_config
        else:
            raw_configurations: dict[str, dict] = kwargs.get("CONNECTIONS", {})
            for connection_name, connection_settings in raw_configurations.items():
                parsed_configuration = AgentAuthConfiguration(
                    **connection_settings.get("SETTINGS", {})
                )
                self._connections[connection_name] = provider_factory(
                    parsed_configuration
                )
                self._config_map[connection_name] = parsed_configuration

        # JWT-patch
        for connection_name, config in self._config_map.items():
            config._connections = self._config_map

        if not self._connections.get("SERVICE_CONNECTION", None):
            raise ValueError("No service connection configuration provided.")

        _log_config(logger, self._config_map, self._connections_map)

    def get_connection(self, connection_name: str | None) -> AccessTokenProviderBase:
        """
        Get the OAuth connection for the agent.

        :param connection_name: The name of the connection.
        :type connection_name: str | None
        :return: The OAuth connection for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AccessTokenProviderBase`
        """
        original_name = connection_name
        connection_name = connection_name or "SERVICE_CONNECTION"
        connection = self._connections.get(connection_name, None)
        if not connection:
            if original_name:
                raise ValueError(f"No connection found for '{original_name}'.")
            else:
                raise ValueError(
                    "No default service connection found. Expected 'SERVICE_CONNECTION'."
                )
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

    @staticmethod
    def _service_url_matches(pattern: str, service_url: str) -> bool:
        """Return whether a SERVICEURL map pattern matches the service URL.

        ``"*"``/empty match any URL. Otherwise the pattern is treated as a regex
        and matched with an unanchored search, mirroring the .NET
        ``ConfigurationConnections`` which uses ``Regex.Match``.

        :raises ValueError: If the pattern is not a valid regex.
        """
        if pattern == "*" or pattern == "":
            return True
        try:
            return re.search(pattern, service_url, re.IGNORECASE) is not None
        except re.error as exc:
            raise ValueError(
                f"Invalid SERVICEURL regex '{pattern}' in connections map: {exc}"
            ) from exc
        
    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent.

        :param claims_identity: The claims identity of the bot.
        :type claims_identity: :class:`microsoft_agents.hosting.core.ClaimsIdentity`
        :param service_url: The service URL of the bot.
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

            if audience_match and self._service_url_matches(
                item.get("SERVICEURL", ""), service_url
            ):
                return self.get_connection(item.get("CONNECTION"))

        raise ValueError(
            f"No connection found for audience '{aud}' and serviceUrl '{service_url}'."
        )
    
    def get_token_provider_from_activity(
            self,
            claims_identity: ClaimsIdentity,
            activity: Activity
            ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent from an activity.

        :param claims_identity: The claims identity of the bot.
        :type claims_identity: :class:`microsoft_agents.hosting.core.ClaimsIdentity`
        :param activity: The activity of the bot.
        :type activity: dict
        :return: The OAuth token provider for the agent.
        :rtype: :class:`microsoft_agents.hosting.core.AccessTokenProviderBase`
        :raises ValueError: If no connection is found for the given audience and service URL.
        """
        connection: AccessTokenProviderBase | None = None
        try:
            connection = self.get_token_provider(claims_identity, activity.service_url)
        finally:
            if (connection is not None and (
                activity.recipient.role == RoleTypes.agentic_identity or
                activity.recipient.role == RoleTypes.agentic_user
            )):
                if connection.configuration.ALT_BLUEPRINT_ID:
                    connection = self.get_connection(connection.configuration.ALT_BLUEPRINT_ID)
                
        if connection:
            return connection
        
        raise RuntimeError(
            "The connection returned by get_token_provider is not compatible with the activity's recipient role."
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

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    ConnectionManager,
)

from .msal_auth import MsalAuth

class MsalConnectionManager(ConnectionManager):
    """
    Connection manager that uses :class:`MsalAuth` as the token provider.

    Thin convenience subclass of the generic
    :class:`microsoft_agents.hosting.core.ConnectionManager` that defaults the
    ``provider_factory`` to :class:`MsalAuth`. All connection routing logic lives
    in the base class.
    """

    def __init__(
        self,
        connections_configurations: dict[str, AgentAuthConfiguration] | None = None,
        connections_map: list[dict[str, str]] | None = None,
        **kwargs,
    ):
        """
        Initialize the MSAL connection manager.

        :param connections_configurations: A dictionary of connection configurations.
        :type connections_configurations: dict[str, :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`]
        :param connections_map: A list of connection mappings.
        :type connections_map: list[dict[str, str]]
        :raises ValueError: If no service connection configuration is provided.
        """

        super().__init__(
            provider_factory=MsalAuth,
            connections_configurations=connections_configurations,
            connections_map=connections_map,
            **kwargs,
        )

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol

from .agent_auth_configuration import AgentAuthConfiguration
from .access_token_provider_base import AccessTokenProviderBase
from .claims_identity import ClaimsIdentity


class Connections(Protocol):

    @abstractmethod
    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        """
        Get the OAuth connection for the agent.

        :param connection_name: The name of the connection.
        :return: The access token provider for the agent.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default OAuth connection for the agent.

        :return: The access token provider for the agent.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent.

        :param claims_identity: The claims identity of the agent.
        :param service_url: The service URL for which to get the token provider.
        :return: The access token provider for the agent.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        """
        Get the default connection configuration for the agent.

        :return: The default connection configuration for the agent.
        """
        raise NotImplementedError()

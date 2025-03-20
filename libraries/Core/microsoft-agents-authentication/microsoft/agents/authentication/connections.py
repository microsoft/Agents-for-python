from abc import abstractmethod
from typing import Protocol

from .access_token_provider_base import AccessTokenProviderBase
from .claims_identity import ClaimsIdentity


class Connections(Protocol):

    @abstractmethod
    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        """
        Get the OAuth connection for the agent.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default OAuth connection for the agent.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get the OAuth token provider for the agent.
        """
        raise NotImplementedError()

from typing import Protocol
from abc import abstractmethod


class AccessTokenProviderBase(Protocol):
    @abstractmethod
    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        """
        Used by Agents SDK to acquire access tokens for connection to agent services or clients.

        :param resource_url: The resource URL for which to get the token.
        :param scopes: The scopes for which to get the token.
        :param force_refresh: True to force a refresh of the token; or false to get the token only if it is necessary.
        :return: The access token as a string.
        """
        pass

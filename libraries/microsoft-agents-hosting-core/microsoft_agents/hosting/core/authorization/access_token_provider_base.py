# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol, Optional
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

    async def acquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        """
        Acquire a token on behalf of a user.

        :param scopes: The scopes for which to get the token.
        :param user_assertion: The user assertion token.
        :return: The access token as a string.
        """
        raise NotImplementedError()

    async def get_agentic_application_token(
        self, agent_app_instance_id: str
    ) -> Optional[str]:
        raise NotImplementedError()

    async def get_agentic_instance_token(
        self, agent_app_instance_id: str
    ) -> tuple[str, str]:
        raise NotImplementedError()

    async def get_agentic_user_token(
        self, agent_app_instance_id: str, agentic_user_id: str, scopes: list[str]
    ) -> Optional[str]:
        raise NotImplementedError()

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging

from azure.core.credentials import TokenCredential, AccessToken
from azure.core.credentials_async import AsyncTokenCredential

from microsoft_agents.hosting.core import AgentAuthConfiguration

from .msal_auth import MsalAuth

logger = logging.getLogger(__name__)


class AsyncMsalTokenCredential(AsyncTokenCredential):
    """AsyncMsalTokenCredential provides an asynchronous implementation for acquiring access tokens using MSAL."""

    def __init__(self, config: AgentAuthConfiguration):
        """Initializes the MsalTokenCredential with the given configuration.

        :param config: The agent authentication configuration.
        :type config: :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`
        """
        self._config = config

    async def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        """Acquire an access token for the specified scopes.

        :param scopes: The scopes for which the access token is requested.
        :param kwargs: Additional keyword arguments.

        :return: The acquired access token.
        :rtype: AccessToken
        """

        logger.debug("get_token scope=%s", scopes)

        if not scopes:
            raise ValueError("At least one scope must be provided.")

        provider = MsalAuth(self._config)

        token = await provider.get_access_token(scopes[0], list(scopes))
        return AccessToken(token, 0)


class MsalTokenCredential(TokenCredential):
    """MsalTokenCredential provides a synchronous wrapper around AsyncMsalTokenCredential for acquiring access tokens."""

    def __init__(self, config: AgentAuthConfiguration):
        """Initializes the MsalTokenCredential with the given configuration.

        :param config: The agent authentication configuration.
        :type config: :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`
        """
        self._config = config
        self._async_credential = AsyncMsalTokenCredential(config)

    def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        """Acquire an access token for the specified scopes.

        :param scopes: The scopes for which the access token is requested.
        :param kwargs: Additional keyword arguments.

        :return: The acquired access token.
        :rtype: AccessToken
        """
        return asyncio.run(self._async_credential.get_token(*scopes, **kwargs))

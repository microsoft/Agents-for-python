# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential

from microsoft_agents.hosting.core import AgentAuthConfiguration

from .msal_auth import MsalAuth

logger = logging.getLogger(__name__)


def _get_resource(scope: str) -> str:
    """Extracts the resource by removing a trailing '/.default' from the scope.

    :param scope: The scope string.
    :return: The extracted resource string.
    :rtype: str
    """
    return scope.removesuffix("/.default")


class MsalTokenCredential(AsyncTokenCredential):
    """Provides an asynchronous Azure Core token credential using MSAL."""

    def __init__(self, config: AgentAuthConfiguration):
        """Initializes the MsalTokenCredential with the given configuration.

        :param config: The agent authentication configuration.
        :type config: :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`
        """
        self._config = config
        self._provider: MsalAuth | None = None

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

        if not self._provider:
            self._provider = MsalAuth(self._config)

        resource = _get_resource(scopes[0])

        return await self._provider._get_access_token(resource, list(scopes))

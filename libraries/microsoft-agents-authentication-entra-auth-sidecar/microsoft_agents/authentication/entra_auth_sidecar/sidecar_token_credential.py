# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from types import TracebackType

from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential

from microsoft_agents.hosting.core import AgentAuthConfiguration

from .sidecar_auth import SidecarAuth
from ._token_expiry import SidecarTokenExpiry

logger = logging.getLogger(__name__)


def _get_resource(scope: str) -> str:
    """Extracts the resource by removing a trailing '/.default' from the scope.

    :param scope: The scope string.
    :return: The extracted resource string.
    :rtype: str
    """
    return scope.removesuffix("/.default")


class SidecarTokenCredential(AsyncTokenCredential):
    """Provides an asynchronous Azure Core token credential using the Sidecar."""

    def __init__(
        self,
        config: AgentAuthConfiguration,
        *,
        provider: SidecarAuth | None = None,
    ):
        """Initializes the SidecarTokenCredential with the given configuration.

        :param config: The agent authentication configuration.
        :type config: :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`
        """
        self._config = config
        self._provider: SidecarAuth | None = provider
        self._manage_provider_lifetime = provider is None

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
            self._provider = SidecarAuth(self._config)

        resource = _get_resource(scopes[0])

        token = await self._provider.get_access_token(resource, list(scopes))

        return AccessToken(
            token=token, expires_on=int(SidecarTokenExpiry.resolve(token).timestamp())
        )

    async def close(self) -> None:
        """Close the credential, releasing any resources.

        :return: None
        :rtype: None
        """
        if self._provider and self._manage_provider_lifetime:
            await self._provider.close()
            self._provider = None

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self.close()

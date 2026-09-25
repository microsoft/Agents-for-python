# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential

from .access_token_provider_base import AccessTokenProviderBase
from .agent_auth_configuration import AgentAuthConfiguration
from ._helpers import _CallableTokenCredential

_ANONYMOUS_TOKEN_EXPIRATION = 2**31 - 1


class AnonymousTokenProvider(AccessTokenProviderBase):
    """
    A class that provides an anonymous token for authentication.
    This is used when no authentication is required.
    """

    @property
    def configuration(self) -> AgentAuthConfiguration:
        """
        The configuration for the access token provider.
        :return: The configuration for the access token provider.
        """
        return AgentAuthConfiguration()

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return ""

    def get_token_credential(self) -> AsyncTokenCredential:
        async def get_token(*scopes: str, **kwargs) -> AccessToken:
            return AccessToken("", _ANONYMOUS_TOKEN_EXPIRATION)

        return _CallableTokenCredential(get_token)

    async def acquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        return ""

    async def get_agentic_application_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> Optional[str]:
        return ""

    async def get_agentic_instance_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> tuple[str, str]:
        return "", ""

    async def get_agentic_user_token(
        self,
        tenant_id: str,
        agent_app_instance_id: str,
        agentic_user_id: str,
        scopes: list[str],
    ) -> Optional[str]:
        return ""

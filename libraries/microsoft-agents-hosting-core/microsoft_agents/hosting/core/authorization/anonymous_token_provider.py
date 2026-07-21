# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from .agent_auth_configuration import AgentAuthConfiguration
from .access_token_provider_base import AccessTokenProviderBase


class AnonymousTokenProvider(AccessTokenProviderBase):
    """
    A class that provides an anonymous token for authentication.
    This is used when no authentication is required.
    """

    @property
    def configuration(self) -> AgentAuthConfiguration:
        """
        The configuration for the anonymous token provider.
        Since this provider does not require any configuration, it returns None.
        """
        return AgentAuthConfiguration()

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return ""

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

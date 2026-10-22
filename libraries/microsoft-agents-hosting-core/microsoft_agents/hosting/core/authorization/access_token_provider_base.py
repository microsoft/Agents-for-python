# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from abc import abstractmethod

from azure.core.credentials_async import AsyncTokenCredential

if TYPE_CHECKING:
    from .connections import AgentAuthConfiguration, ConnectionSettingsBase


class AccessTokenProviderBase(Protocol):

    @property
    def configuration(self) -> AgentAuthConfiguration:
        """
        Deprecated legacy configuration view. Prefer :attr:`config`.

        :return: AgentAuthConfiguration retained for compatibility.
        """
        # this property is deprecated and will be removed in future versions
        raise NotImplementedError()

    @property
    @abstractmethod
    def config(self) -> ConnectionSettingsBase:
        """
        Bound provider-specific settings extending ConnectionSettingsBase.

        :return: The provider's typed connection settings.
        """
        from .connections.connection_settings_base import ConnectionSettingsBase

        return ConnectionSettingsBase(**self.configuration._to_dict())

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

    @abstractmethod
    def get_token_credential(self) -> AsyncTokenCredential:
        """
        Get the token credential for the access token provider.

        :return: The token credential.
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
        self, tenant_id: str, agent_app_instance_id: str
    ) -> str | None:
        raise NotImplementedError()

    async def get_agentic_instance_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> tuple[str, str]:
        raise NotImplementedError()

    async def get_agentic_user_token(
        self,
        tenant_id: str,
        agent_app_instance_id: str,
        agentic_user_id: str,
        scopes: list[str],
    ) -> str | None:
        raise NotImplementedError()

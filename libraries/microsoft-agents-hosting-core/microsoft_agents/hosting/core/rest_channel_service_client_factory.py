# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
import logging

from microsoft_agents.activity import RoleTypes
from microsoft_agents.hosting.core.authorization import (
    AuthenticationConstants,
    AnonymousTokenProvider,
    ClaimsIdentity,
    Connections,
)
from microsoft_agents.hosting.core.authorization import AccessTokenProviderBase
from microsoft_agents.hosting.core.connector import ConnectorClientBase
from microsoft_agents.hosting.core.connector.client import UserTokenClient
from microsoft_agents.hosting.core.connector.teams import TeamsConnectorClient

from .channel_service_client_factory_base import ChannelServiceClientFactoryBase
from .turn_context import TurnContext

logger = logging.getLogger(__name__)


class RestChannelServiceClientFactory(ChannelServiceClientFactoryBase):
    _ANONYMOUS_TOKEN_PROVIDER = AnonymousTokenProvider()

    def __init__(
        self,
        connection_manager: Connections,
        token_service_endpoint=AuthenticationConstants.AGENTS_SDK_OAUTH_URL,
        token_service_audience=AuthenticationConstants.AGENTS_SDK_SCOPE,
    ) -> None:
        self._connection_manager = connection_manager
        self._token_service_endpoint = token_service_endpoint
        self._token_service_audience = token_service_audience

    async def _get_agentic_token(self, context: TurnContext, service_url: str) -> str:
        logger.info(
            "Creating connector client for agentic request to service_url: %s",
            service_url,
        )

        if not context.identity:
            raise ValueError("context.identity is required for agentic activities")

        connection = self._connection_manager.get_token_provider(
            context.identity, service_url
        )
        if not hasattr(connection, "_msal_configuration"):
            raise TypeError(
                "Connection does not support MSAL configuration for agentic token retrieval"
            )

        if connection._msal_configuration.ALT_BLUEPRINT_ID:
            logger.debug(
                "Using alternative blueprint ID for agentic token retrieval: %s",
                connection._msal_configuration.ALT_BLUEPRINT_ID,
            )
            connection = self._connection_manager.get_connection(
                connection._msal_configuration.ALT_BLUEPRINT_ID
            )

        agent_instance_id = context.activity.get_agentic_instance_id()
        if not agent_instance_id:
            raise ValueError("Agent instance ID is required for agentic identity role")

        if context.activity.recipient.role == RoleTypes.agentic_identity:
            token, _ = await connection.get_agentic_instance_token(agent_instance_id)
        else:
            agentic_user = context.activity.get_agentic_user()
            if not agentic_user:
                raise ValueError("Agentic user is required for agentic user role")
            token = await connection.get_agentic_user_token(
                agent_instance_id,
                agentic_user,
                [AuthenticationConstants.APX_PRODUCTION_SCOPE],
            )

        if not token:
            raise ValueError("Failed to obtain token for agentic activity")
        return token

    async def create_connector_client(
        self,
        context: TurnContext,
        claims_identity: ClaimsIdentity,
        service_url: str,
        audience: str,
        scopes: Optional[list[str]] = None,
        use_anonymous: bool = False,
    ) -> ConnectorClientBase:
        if not context or not claims_identity:
            raise TypeError("context and claims_identity are required")
        if not service_url:
            raise TypeError(
                "RestChannelServiceClientFactory.create_connector_client: service_url can't be None or Empty"
            )
        if not audience:
            raise TypeError(
                "RestChannelServiceClientFactory.create_connector_client: audience can't be None or Empty"
            )

        if context.activity.is_agentic_request():
            token = await self._get_agentic_token(context, service_url)
        else:
            token_provider: AccessTokenProviderBase = (
                self._connection_manager.get_token_provider(
                    claims_identity, service_url
                )
                if not use_anonymous
                else self._ANONYMOUS_TOKEN_PROVIDER
            )

            token = await token_provider.get_access_token(
                audience, scopes or [f"{audience}/.default"]
            )

        return TeamsConnectorClient(
            endpoint=service_url,
            token=token,
        )

    async def create_user_token_client(
        self,
        context: TurnContext,
        claims_identity: ClaimsIdentity,
        use_anonymous: bool = False,
    ) -> UserTokenClient:
        """Create a UserTokenClient for the given context and claims identity.

        :param context: The TurnContext for the current turn of conversation.
        :param claims_identity: The ClaimsIdentity of the user.
        :param use_anonymous: Whether to use an anonymous token provider.
        """
        if not context or not claims_identity:
            raise ValueError("context and claims_identity are required")

        if use_anonymous:
            return UserTokenClient(endpoint=self._token_service_endpoint, token="")

        if context.activity.is_agentic_request():
            token = await self._get_agentic_token(context, self._token_service_endpoint)
        else:
            scopes = [f"{self._token_service_audience}/.default"]

            token_provider = self._connection_manager.get_token_provider(
                claims_identity, self._token_service_endpoint
            )

            token = await token_provider.get_access_token(
                self._token_service_audience, scopes
            )

        if not token:
            logger.error("Failed to obtain token for user token client")
            raise ValueError("Failed to obtain token for user token client")

        return UserTokenClient(
            endpoint=self._token_service_endpoint,
            token=token,
        )

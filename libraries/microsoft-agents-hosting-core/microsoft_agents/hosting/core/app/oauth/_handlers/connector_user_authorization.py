"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging
import jwt
from datetime import datetime, timezone
from typing import Optional

from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core.errors import ErrorResources

from ...._oauth._flow_state import _FlowStateTag
from ....turn_context import TurnContext
from ....storage import Storage
from ....authorization import Connections
from ..auth_handler import AuthHandler
from ._authorization_handler import _AuthorizationHandler
from .._sign_in_response import _SignInResponse

logger = logging.getLogger(__name__)


class ConnectorUserAuthorization(_AuthorizationHandler):
    """
    User Authorization handling for Copilot Studio Connector requests.
    Extracts token from the identity and performs OBO token exchange.
    """

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handler: Optional[AuthHandler] = None,
        *,
        auth_handler_id: Optional[str] = None,
        auth_handler_settings: Optional[dict] = None,
        **kwargs,
    ) -> None:
        """
        Creates a new instance of ConnectorUserAuthorization.

        :param storage: The storage system to use for state management.
        :type storage: Storage
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: Connections
        :param auth_handler: Configuration for OAuth provider.
        :type auth_handler: AuthHandler, Optional
        :param auth_handler_id: Optional ID of the auth handler.
        :type auth_handler_id: str, Optional
        :param auth_handler_settings: Optional settings dict for the auth handler.
        :type auth_handler_settings: dict, Optional
        """
        super().__init__(
            storage,
            connection_manager,
            auth_handler,
            auth_handler_id=auth_handler_id,
            auth_handler_settings=auth_handler_settings,
            **kwargs,
        )

    async def _sign_in(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> _SignInResponse:
        """
        For connector requests, there is no separate sign-in flow.
        The token is extracted from the identity.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param scopes: Optional list of scopes (unused for connector auth).
        :type scopes: Optional[list[str]], Optional
        :return: A SignInResponse with the extracted token.
        :rtype: _SignInResponse
        """
        # Connector auth uses the token from the request, not a separate sign-in flow
        token_response = await self.get_refreshed_token(context)
        return _SignInResponse(
            token_response=token_response, tag=_FlowStateTag.COMPLETE
        )

    async def get_refreshed_token(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> TokenResponse:
        """
        Gets the connector user token and optionally exchanges it via OBO.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param exchange_connection: Optional name of the connection to use for token exchange.
        :type exchange_connection: Optional[str], Optional
        :param exchange_scopes: Optional list of scopes to request during token exchange.
        :type exchange_scopes: Optional[list[str]], Optional
        :return: The token response, potentially after OBO exchange.
        :rtype: TokenResponse
        """
        token_response = self._create_token_response(context)

        # Check if token is expired
        if token_response.expiration:
            try:
                # Parse ISO 8601 format
                expiration = datetime.fromisoformat(
                    token_response.expiration.replace("Z", "+00:00")
                )
                if expiration <= datetime.now(timezone.utc):
                    raise ValueError(
                        f"Unexpected connector token expiration for handler: {self._id}"
                    )
            except (ValueError, AttributeError) as ex:
                logger.error(
                    f"Error checking token expiration for handler {self._id}: {ex}"
                )
                raise

        # Perform OBO exchange if configured
        try:
            return await self._handle_obo(
                context, token_response, exchange_connection, exchange_scopes
            )
        except Exception:
            await self._sign_out(context)
            raise

    async def _sign_out(self, context: TurnContext) -> None:
        """
        Sign-out is a no-op for connector authorization.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        """
        # No concept of sign-out with ConnectorAuth
        logger.debug("Sign-out called for ConnectorUserAuthorization (no-op)")

    async def _handle_obo(
        self,
        context: TurnContext,
        input_token_response: TokenResponse,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> TokenResponse:
        """
        Exchanges a token for another token with different scopes via OBO flow.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param input_token_response: The input token to exchange.
        :type input_token_response: TokenResponse
        :param exchange_connection: Optional connection name for exchange.
        :type exchange_connection: Optional[str]
        :param exchange_scopes: Optional scopes for the exchanged token.
        :type exchange_scopes: Optional[list[str]]
        :return: The token response after exchange, or the original if exchange not configured.
        :rtype: TokenResponse
        """
        if not input_token_response:
            return input_token_response

        connection_name = exchange_connection or self._handler.obo_connection_name
        scopes = exchange_scopes or self._handler.scopes

        # If OBO is not configured, return token as-is
        if not connection_name or not scopes:
            return input_token_response

        # Check if token is exchangeable
        if not input_token_response.is_exchangeable():
            raise ValueError(
                str(ErrorResources.OboNotExchangeableToken.format(self._id))
            )

        # Get the connection that supports OBO
        token_provider = self._connection_manager.get_connection(connection_name)
        if not token_provider:
            raise ValueError(
                str(
                    ErrorResources.ResourceNotFound.format(
                        f"Connection '{connection_name}'"
                    )
                )
            )

        # Perform the OBO exchange
        # Note: In Python, the acquire_token_on_behalf_of method is on the AccessTokenProviderBase
        token = await token_provider.acquire_token_on_behalf_of(
            scopes=scopes,
            user_assertion=input_token_response.token,
        )
        return TokenResponse(token=token) if token else None

    def _create_token_response(self, context: TurnContext) -> TokenResponse:
        """
        Creates a TokenResponse from the security token in the turn context identity.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :return: A TokenResponse containing the extracted token.
        :rtype: TokenResponse
        :raises ValueError: If the identity doesn't have a security token.
        """
        if not context.identity or not hasattr(context.identity, "security_token"):
            raise ValueError(
                f"Unexpected connector request - no security token found for handler: {self._id}"
            )

        security_token = context.identity.security_token
        if not security_token:
            raise ValueError(
                f"Unexpected connector request - security token is None for handler: {self._id}"
            )

        token_response = TokenResponse(token=security_token)

        # Try to extract expiration and check if exchangeable
        try:
            # TODO: (connector) validate this decoding
            jwt_token = jwt.decode(security_token, options={"verify_signature": False})

            # Set expiration if present
            if "exp" in jwt_token:
                # JWT exp is in Unix timestamp (seconds since epoch)
                expiration = datetime.fromtimestamp(jwt_token["exp"], tz=timezone.utc)
                # Convert to ISO 8601 format
                token_response.expiration = expiration.isoformat()

        except Exception as ex:
            logger.warning(f"Failed to parse JWT token for handler {self._id}: {ex}")
            raise ex
            # If we can't parse the token, we'll still return it without expiration info

        return token_response

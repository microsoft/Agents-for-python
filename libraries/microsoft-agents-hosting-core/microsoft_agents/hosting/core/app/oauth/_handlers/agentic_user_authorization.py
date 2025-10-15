"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging

from typing import Optional

from microsoft_agents.activity import TokenResponse

from ....turn_context import TurnContext
from ...._oauth import _FlowStateTag
from .._sign_in_response import _SignInResponse
from ._authorization_handler import _AuthorizationHandler
from ....storage import Storage
from ....authorization import Connections
from ..auth_handler import AuthHandler

logger = logging.getLogger(__name__)


class AgenticUserAuthorization(_AuthorizationHandler):
    """Class responsible for managing agentic authorization"""

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
        Creates a new instance of Authorization.

        :param storage: The storage system to use for state management.
        :type storage: Storage
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: Connections
        :param auth_handlers: Configuration for OAuth providers.
        :type auth_handlers: dict[str, AuthHandler], Optional
        :raises ValueError: When storage is None or no auth handlers provided.
        """
        super().__init__(
            storage,
            connection_manager,
            auth_handler,
            auth_handler_id=auth_handler_id,
            auth_handler_settings=auth_handler_settings,
            **kwargs,
        )
        self._alt_blueprint_name = (
            auth_handler._alt_blueprint_name if auth_handler else None
        )

    async def get_agentic_instance_token(self, context: TurnContext) -> TokenResponse:
        """Gets the agentic instance token for the current agent instance.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :return: The agentic instance token, or None if not an agentic request.
        :rtype: Optional[str]
        """

        if not context.activity.is_agentic_request():
            return TokenResponse()

        assert context.identity
        connection = self._connection_manager.get_token_provider(
            context.identity, "agentic"
        )
        agentic_instance_id = context.activity.get_agentic_instance_id()
        assert agentic_instance_id
        instance_token, _ = await connection.get_agentic_instance_token(
            agentic_instance_id
        )
        return (
            TokenResponse(token=instance_token) if instance_token else TokenResponse()
        )

    async def get_agentic_user_token(
        self, context: TurnContext, scopes: list[str]
    ) -> TokenResponse:
        """Gets the agentic user token for the current agent instance and user.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param scopes: The scopes to request for the token.
        :type scopes: list[str]
        :return: The agentic user token, or None if not an agentic request or no user.
        :rtype: Optional[str]
        """
        logger.info("Retrieving agentic user token for scopes: %s", scopes)

        if (
            not context.activity.is_agentic_request()
            or not context.activity.get_agentic_user()
        ):
            return TokenResponse()

        assert context.identity
        if self._alt_blueprint_name:
            logger.debug(
                "Using alternative blueprint name for agentic user token retrieval: %s",
                self._alt_blueprint_name,
            )
            connection = self._connection_manager.get_connection(
                self._alt_blueprint_name
            )
        else:
            logger.debug(
                "Using connection manager for agentic user token retrieval with handler id: %s",
                self._id,
            )
            connection = self._connection_manager.get_token_provider(
                context.identity, "agentic"
            )
        agentic_user_id = context.activity.get_agentic_user()
        agentic_instance_id = context.activity.get_agentic_instance_id()
        if not agentic_user_id or not agentic_instance_id:
            logger.error(
                "Unable to retrieve agentic user token: missing agentic user Id or agentic instance Id. agentic_user_id: %s, Agentic Instance ID: %s",
                agentic_user_id,
                agentic_instance_id,
            )
            raise ValueError(
                f"Unable to retrieve agentic user token: missing agentic User Id or agentic instance Id. agentic_user_id: {agentic_user_id}, Agentic Instance ID: {agentic_instance_id}"
            )

        token = await connection.get_agentic_user_token(
            agentic_instance_id, agentic_user_id, scopes
        )
        return TokenResponse(token=token) if token else TokenResponse()

    async def _sign_in(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> _SignInResponse:
        """Retrieves the agentic user token if available.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param connection_name: The name of the connection to use for sign-in.
        :type connection_name: str
        :param scopes: The scopes to request for the token.
        :type scopes: Optional[list[str]]
        :return: A _SignInResponse containing the token response and flow state tag.
        :rtype: _SignInResponse
        """
        token_response = await self.get_refreshed_token(
            context, exchange_connection, exchange_scopes
        )
        if token_response:
            return _SignInResponse(
                token_response=token_response, tag=_FlowStateTag.COMPLETE
            )
        return _SignInResponse(tag=_FlowStateTag.FAILURE)

    async def get_refreshed_token(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> TokenResponse:
        """Attempts to get a refreshed token for the user with the given scopes

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param exchange_connection: Optional name of the connection to use for token exchange. If None, default connection will be used.
        :type exchange_connection: Optional[str], Optional
        :param exchange_scopes: Optional list of scopes to request during token exchange. If None, default scopes will be used.
        :type exchange_scopes: Optional[list[str]], Optional
        """
        if not exchange_scopes:
            exchange_scopes = self._handler.scopes or []
        return await self.get_agentic_user_token(context, exchange_scopes)

    async def sign_out(
        self, context: TurnContext, auth_handler_id: Optional[str] = None
    ) -> None:
        """Nothing to do for agentic sign out."""

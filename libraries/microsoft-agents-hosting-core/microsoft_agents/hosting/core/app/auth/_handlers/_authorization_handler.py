"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from abc import ABC
from typing import Optional
import logging

from microsoft_agents.activity import TokenResponse

from ....turn_context import TurnContext
from ....storage import Storage
from ....authorization import Connections
from ..auth_handler import AuthHandler
from .._sign_in_response import _SignInResponse

logger = logging.getLogger(__name__)


class _AuthorizationHandler(ABC):
    """Base class for different authorization strategies."""

    _storage: Storage
    _connection_manager: Connections
    _handler: AuthHandler

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
        if not storage:
            raise ValueError("Storage is required for Authorization")
        if not auth_handler and not auth_handler_settings:
            raise ValueError(
                "At least one of auth_handler or auth_handler_settings is required."
            )

        self._storage = storage
        self._connection_manager = connection_manager

        if auth_handler:
            self._handler = auth_handler
        else:
            self._handler = AuthHandler._from_settings(auth_handler_settings)

        self._id = auth_handler_id or self._handler.name
        if not self._id:
            raise ValueError(
                "Auth handler must have an ID. Could not be deduced from settings or constructor args."
            )

    async def _sign_in(
        self, context: TurnContext, scopes: Optional[list[str]] = None
    ) -> _SignInResponse:
        """Initiate or continue the sign-in process for the user with the given auth handler.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param scopes: Optional list of scopes to request during sign-in. If None, default scopes will be used.
        :type scopes: Optional[list[str]], Optional
        :return: A SignInResponse indicating the result of the sign-in attempt.
        :rtype: SignInResponse
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    async def _sign_out(self, context: TurnContext) -> None:
        """Attempts to sign out the user from the specified auth handler or all handlers if none specified.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: Optional[str]
        """
        raise NotImplementedError()

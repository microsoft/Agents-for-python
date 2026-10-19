"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging
import warnings

from abc import ABC

from microsoft_agents.activity import TokenResponse

from ....turn_context import TurnContext
from ....storage import Storage
from ....authorization import Connections
from ..auth_handler import AuthHandlerSettings
from .._sign_in_response import _SignInResponse

logger = logging.getLogger(__name__)


class _AuthorizationHandler(ABC):
    """Base class for different authorization strategies."""

    _storage: Storage
    _connection_manager: Connections
    _handler: AuthHandlerSettings

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        settings: dict | AuthHandlerSettings | None = None,
        *,
        auth_handler_id: str | None = None,
        auth_handler: AuthHandlerSettings | None = None,
        auth_handler_settings: dict | None = None,
        **kwargs,
    ) -> None:
        """
        Creates a new instance of Authorization.

        :param storage: The storage system to use for state management.
        :type storage: Storage
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: Connections
        :param settings: Optional settings for the auth handler.
        :type settings: dict | AuthHandlerSettings | None
        :param auth_handler: (Deprecated) Configuration for OAuth provider.
        :type auth_handler: AuthHandlerSettings | None
        :param auth_handler_id: Optional ID of the auth handler.
        :type auth_handler_id: str | None
        :param auth_handler_settings: (Deprecated) Optional settings dict for the auth handler.
        :type auth_handler_settings: dict | None
        :raises ValueError: When storage is None or no auth handlers provided.
        """
        if not storage:
            raise ValueError("Storage is required for Authorization")
        if not settings and not auth_handler and not auth_handler_settings:
            raise ValueError(
                "At least one of settings or auth_handler or auth_handler_settings is required."
            )
        if auth_handler or auth_handler_settings:
            warnings.warn(
                "auth_handler and auth_handler_settings are deprecated. Please use settings instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self._storage = storage
        self._connection_manager = connection_manager

        if settings:
            if isinstance(settings, dict):
                self._handler = AuthHandlerSettings._from_settings(settings, **kwargs)
            else:
                self._handler = AuthHandlerSettings._from_settings(
                    settings._to_dict(), **kwargs
                )
        elif auth_handler:
            self._handler = AuthHandlerSettings._from_settings(
                auth_handler._to_dict(), **kwargs
            )
        else:
            if not auth_handler_settings:
                raise ValueError(
                    "auth_handler_settings must be provided if auth_handler is None."
                )
            self._handler = AuthHandlerSettings._from_settings(
                auth_handler_settings, **kwargs
            )

        self._id = auth_handler_id or self._handler.name
        if not self._id:
            raise ValueError(
                "Auth handler must have an ID. Could not be deduced from settings or constructor args."
            )

    async def _sign_in(
        self, context: TurnContext, scopes: list[str] | None = None
    ) -> _SignInResponse:
        """Initiate or continue the sign-in process for the user with the given auth handler.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param scopes: Optional list of scopes to request during sign-in. If None, default scopes will be used.
        :type scopes: list[str] | None
        :return: A SignInResponse indicating the result of the sign-in attempt.
        :rtype: SignInResponse
        """
        raise NotImplementedError()

    async def get_refreshed_token(
        self,
        context: TurnContext,
        exchange_connection: str | None = None,
        exchange_scopes: list[str] | None = None,
    ) -> TokenResponse:
        """Attempts to get a refreshed token for the user with the given scopes

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param exchange_connection: Optional name of the connection to use for token exchange. If None, default connection will be used.
        :type exchange_connection: str | None
        :param exchange_scopes: Optional list of scopes to request during token exchange. If None, default scopes will be used.
        :type exchange_scopes: list[str] | None
        """
        raise NotImplementedError()

    async def _sign_out(self, context: TurnContext) -> None:
        """Attempts to sign out the user from the specified auth handler or all handlers if none specified.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: str | None
        """
        raise NotImplementedError()

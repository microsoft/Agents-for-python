from abc import ABC
from typing import Optional
import logging

from ...turn_context import TurnContext
from ...oauth import FlowStateTag
from ...storage import Storage
from ...authorization import Connections
from .auth_handler import AuthHandler
from .sign_in_response import SignInResponse

logger = logging.getLogger(__name__)


class AuthorizationVariant(ABC):
    """Base class for different authorization strategies."""

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: dict[str, AuthHandler] = None,
        auto_signin: bool = None,
        use_cache: bool = False,
        **kwargs,
    ) -> None:
        """
        Creates a new instance of Authorization.

        :param storage: The storage system to use for state management.
        :type storage: Storage
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: Connections
        :param auth_handlers: Configuration for OAuth providers.
        :type auth_handlers: dict[str, AuthHandler], optional
        :raises ValueError: When storage is None or no auth handlers provided.
        """
        if not storage:
            raise ValueError("Storage is required for Authorization")

        self._storage = storage
        self._connection_manager = connection_manager

        auth_configuration: dict = kwargs.get("AGENTAPPLICATION", {}).get(
            "USERAUTHORIZATION", {}
        )

        handlers_config: dict[str, dict] = auth_configuration.get("HANDLERS", {})
        if not auth_handlers and handlers_config:
            auth_handlers = {
                handler_name: AuthHandler(
                    name=handler_name, **config.get("SETTINGS", {})
                )
                for handler_name, config in handlers_config.items()
            }

        self._auth_handlers = auth_handlers or {}

    async def sign_in(
        self, context: TurnContext, auth_handler_id: Optional[str] = None
    ) -> SignInResponse:
        """Initiate or continue the sign-in process for the user with the given auth handler.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to use for sign-in. If None, the first handler will be used.
        :type auth_handler_id: Optional[str]
        :return: A SignInResponse indicating the result of the sign-in attempt.
        :rtype: SignInResponse
        """
        raise NotImplementedError()

    async def sign_out(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None,
    ) -> None:
        """Attempts to sign out the user from the specified auth handler or all handlers if none specified.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: Optional[str]
        """
        raise NotImplementedError()

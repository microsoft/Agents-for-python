from abc import ABC
from typing import Optional
import logging

from microsoft_agents.activity import TokenResponse

from ....turn_context import TurnContext
from ....storage import Storage
from ....authorization import Connections
from ..auth_handler import AuthHandler
from ..sign_in_response import SignInResponse

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

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str],
        auth_handler_id: str,
    ) -> TokenResponse:
        """
        Exchanges a token for another token with different scopes.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param scopes: The scopes to request for the new token.
        :type scopes: list[str]
        :param auth_handler_id: Optional ID of the auth handler to use, defaults to first
        :type auth_handler_id: str
        :return: The token response from the OAuth provider from the exchange.
            If the cached token is not exchangeable, returns the cached token.
        :rtype: TokenResponse
        """
        
        token_response = await self.get_token(context, auth_handler_id)

        if token_response and self._is_exchangeable(token_response.token):
            logger.debug("Token is exchangeable, performing OBO flow")
            return await self._handle_obo(token_response.token, scopes, auth_handler_id)

        return token_response

    def _is_exchangeable(self, token: str) -> bool:
        """
        Checks if a token is exchangeable (has api:// audience).

        :param token: The token to check.
        :type token: str
        :return: True if the token is exchangeable, False otherwise.
        """
        try:
            # Decode without verification to check the audience
            payload = jwt.decode(token, options={"verify_signature": False})
            aud = payload.get("aud")
            return isinstance(aud, str) and aud.startswith("api://")
        except Exception:
            logger.error("Failed to decode token to check audience")
            return False

    async def _handle_obo(
        self, token: str, scopes: list[str], handler_id: str = None
    ) -> TokenResponse:
        """
        Handles On-Behalf-Of token exchange.

        :param token: The original token.
        :type token: str
        :param scopes: The scopes to request.
        :type scopes: list[str]
        :param handler_id: The ID of the auth handler to use, defaults to first
        :type handler_id: str, optional
        :return: The new token response.
        :rtype: TokenResponse
        """
        auth_handler = self.resolve_handler(handler_id)
        token_provider = self._connection_manager.get_connection(
            auth_handler.obo_connection_name
        )

        logger.info("Attempting to exchange token on behalf of user")
        new_token = await token_provider.aquire_token_on_behalf_of(
            scopes=scopes,
            user_assertion=token,
        )
        return TokenResponse(token=new_token)

    async def sign_in(
        self, context: TurnContext, auth_handler_id: str, scopes: Optional[list[str]] = None
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


import jwt
from abc import ABC
from typing import TypeVar, Optional, Generic
import logging

from microsoft_agents.activity import (
    TokenResponse,
)

from ...turn_context import TurnContext
from ...storage import Storage
from ...authorization import Connections, AccessTokenProviderBase
from ..state.turn_state import TurnState
from .auth_handler import AuthHandler

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)

class AuthorizationVariant(ABC, Generic[StateT]):

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: dict[str, AuthHandler] = None,
        auto_signin: bool = None,
        use_cache: bool = False,
        **kwargs,
    ):
        """
        Creates a new instance of Authorization.

        Args:
            storage: The storage system to use for state management.
            auth_handlers: Configuration for OAuth providers.

        Raises:
            ValueError: If storage is None or no auth handlers are provided.
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

    
    async def get_token(
        self, context: TurnContext, auth_handler_id: str
    ) -> TokenResponse:
        raise NotImplementedError() 
        
    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str],
        auth_handler_id: Optional[str] = None,
    ) -> TokenResponse:
        raise NotImplementedError()
    
    def _is_exchangeable(self, token: str) -> bool:
        """
        Checks if a token is exchangeable (has api:// audience).

        Args:
            token: The token to check.

        Returns:
            True if the token is exchangeable, False otherwise.
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

        Args:
            context: The context object for the current turn.
            token: The original token.
            scopes: The scopes to request.

        Returns:
            The new token response.

        """
        auth_handler = self.resolve_handler(handler_id)
        token_provider: AccessTokenProviderBase = (
            self._connection_manager.get_connection(auth_handler.obo_connection_name)
        )

        logger.info("Attempting to exchange token on behalf of user")
        new_token = await token_provider.aquire_token_on_behalf_of(
            scopes=scopes,
            user_assertion=token,
        )
        return TokenResponse(token=new_token)

    def resolve_handler(self, auth_handler_id: Optional[str] = None) -> AuthHandler:
        """Resolves the auth handler to use based on the provided ID.

        Args:
            auth_handler_id: Optional ID of the auth handler to resolve, defaults to first handler.

        Returns:
            The resolved auth handler.
        """
        if auth_handler_id:
            if auth_handler_id not in self._auth_handlers:
                logger.error("Auth handler '%s' not found", auth_handler_id)
                raise ValueError(f"Auth handler '{auth_handler_id}' not found")
            return self._auth_handlers[auth_handler_id]

        # Return the first handler if no ID specified
        return next(iter(self._auth_handlers.values()))

    async def sign_out(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None,
    ) -> None:
        raise NotImplementedError()
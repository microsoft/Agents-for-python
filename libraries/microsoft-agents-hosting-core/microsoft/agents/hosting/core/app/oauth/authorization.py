# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
import jwt
from typing import Dict, Optional, Callable, Awaitable
from collections.abc import Iterable

from microsoft.agents.hosting.core.authorization import (
    Connections,
    AccessTokenProviderBase,
)
from microsoft.agents.hosting.core.storage import Storage
from microsoft.agents.activity import TokenResponse, Activity
from microsoft.agents.hosting.core.storage import StoreItem
from pydantic import BaseModel

from ...turn_context import TurnContext
from ...app.state.turn_state import TurnState
from ...oauth_flow import OAuthFlow, FlowState
from ...state.user_state import UserState
from .sign_in_context import SignInContext
from .auth_handler import AuthHandler, AuthorizationHandlers
from .sign_in_state import SignInState

from .storage import AuthStateStorage

logger = logging.getLogger(__name__)


class Authorization:
    """
    Class responsible for managing authorization and OAuth flows.
    Handles multiple OAuth providers and manages the complete authentication lifecycle.
    """

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: AuthorizationHandlers = None,
        auto_signin: bool = None,
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
        if not auth_handlers:
            raise ValueError("At least one AuthHandler must be provided")

        user_state = UserState(storage)

        self.__auth_storage = AuthStateStorage(storage, )

        self._connection_manager = connection_manager

        auth_configuration: Dict = kwargs.get("AGENTAPPLICATION", {}).get(
            "USERAUTHORIZATION", {}
        )

        self._auto_signin = (
            auto_signin
            if auto_signin is not None
            else auth_configuration.get("AUTOSIGNIN", False)
        )

        handlers_config: Dict[str, Dict] = auth_configuration.get("HANDLERS")
        if not auth_handlers and handlers_config:
            auth_handlers = {
                handler_name: AuthHandler(
                    name=handler_name, **config.get("SETTINGS", {})
                )
                for handler_name, config in handlers_config.items()
            }

        self._auth_handlers = auth_handlers or {}
        self._sign_in_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None
        self._sign_in_failed_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None

        # Configure each auth handler
        for auth_handler in self._auth_handlers.values():
            # Create OAuth flow with configuration
            messages_config = {}
            if auth_handler.title:
                messages_config["card_title"] = auth_handler.title
            if auth_handler.text:
                messages_config["button_text"] = auth_handler.text

            logger.debug(f"Configuring OAuth flow for handler: {auth_handler.name}")
            auth_handler.flow = OAuthFlow(
                storage=storage,
                abs_oauth_connection_name=auth_handler.abs_oauth_connection_name,
                messages_configuration=messages_config if messages_config else None,
            )

    async def get_token(
        self, context: TurnContext, auth_handler_id: Optional[str] = None
    ) -> TokenResponse:
        """
        Gets the token for a specific auth handler.

        Args:
                      context: The context object for the current turn.
  auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        flow = OAuthFlow(context, auth_handler_id)
        return await flow.get_token()

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str],
        auth_handler_id: Optional[str] = None,
    ) -> TokenResponse:
        """
        Exchanges a token for another token with different scopes.

        Args:
            context: The context object for the current turn.
            scopes: The scopes to request for the new token.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        flow = OAuthFlow(context, auth_handler_id)

        token_response = await flow.get_user_token(context)

        if self.__is_exchangeable(token_response.token if token_response else None):
            pass

        return await flow.exchange_token(scopes)

        # auth_handler = self.resolver_handler(auth_handler_id)
        # if not auth_handler.flow:
        #     logger.error("OAuth flow is not configured for the auth handler")
        #     raise ValueError("OAuth flow is not configured for the auth handler")

        # token_response = await auth_handler.flow.get_user_token(context)

        # if self._is_exchangeable(token_response.token if token_response else None):
        #     return await self._handle_obo(token_response.token, scopes, auth_handler_id)

        # return token_response

    def _is_exchangeable(self, token: Optional[str]) -> bool:
        """
        Checks if a token is exchangeable (has api:// audience).

        Args:
            token: The token to check.

        Returns:
            True if the token is exchangeable, False otherwise.
        """
        if not token:
            return False

        try:
            # Decode without verification to check the audience
            payload = jwt.decode(token, options={"verify_signature": False})
            aud = payload.get("aud")
            return isinstance(aud, str) and aud.startswith("api://")
        except Exception:
            logger.exception("Failed to decode token to check audience")
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
        if not self._connection_manager:
            logger.error("Connection manager is not configured", stack_info=True)
            raise ValueError("Connection manager is not configured")

        auth_handler = self.resolver_handler(handler_id)
        if auth_handler.flow is None:
            logger.error("OAuth flow is not configured for the auth handler")
            raise ValueError("OAuth flow is not configured for the auth handler")

        # Use the flow's OBO method to exchange the token
        token_provider: AccessTokenProviderBase = (
            self._connection_manager.get_connection(auth_handler.obo_connection_name)
        )
        logger.info("Attempting to exchange token on behalf of user")
        token = await token_provider.aquire_token_on_behalf_of(
            scopes=scopes,
            user_assertion=token,
        )
        return TokenResponse(
            token=token,
            scopes=scopes,  # Expiration can be set based on the token provider's response
        )

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        turn_state: TurnState,
        auth_handler_id: str,
        sec_route: bool = True,
    ) -> AuthFlowResponse:
        """
        Begins or continues an OAuth flow.

        Args:
            context: The context object for the current turn.
            state: The state object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        # robrandao: TODO -> is_started_from_route and sec_route

        flow_storage_client = FlowStorageClient(context, self.__storage)
        flow = self.__create_flow(context, auth_handler_id)


        sign_in_context: SignInContext = self.__create_sign_in_context(
            context, auth_handler_id, 42
        )
        if self.__sign_in_success_handler:
            sign_in_context.on_success(
                lambda: self.__sign_in_success_handler(
                    context, turn_state, sign_in_context.handler.id
                )
            )
        if self.__sign_in_failure_handler:
            sign_in_context.on_failure(
                lambda err: self.__sign_in_failure_handler(
                    context, turn_state, sign_in_context.handler.id, err
                )
            )

        async for activity in auth_handler.begin_or_continue_flow():
            pass

        token_response = await sign_in_context.get_token()
        return BeginOrContinueFlowResponse(token_response, sign_in_context.handler)

    def resolve_handler(self, auth_handler_id: Optional[str] = None) -> AuthHandler:
        """
        Resolves the auth handler to use based on the provided ID.

        Args:
            auth_handler_id: Optional ID of the auth handler to resolve, defaults to first handler.

        Returns:
            The resolved auth handler.
        """
        if auth_handler_id:
            if auth_handler_id not in self._auth_handlers:
                logger.error(f"Auth handler '{auth_handler_id}' not found")
                raise ValueError(f"Auth handler '{auth_handler_id}' not found")
            return self._auth_handlers[auth_handler_id]

        # Return the first handler if no ID specified
        return next(iter(self._auth_handlers.values))
    
    async def __sign_out(
        self,
        context: TurnContext,
        state: TurnState,
        auth_handler_ids: Iterable[str] = None,
    ) -> None:
        flow_storage_client = FlowStorageClient(context, self.__storage)
        for auth_handler_id in auth_handler_ids:
            auth_handler = self.resolver_handler(auth_handler_id)
            flow_state = flow_storage_client.read(auth_handler.flow_id)
            if flow_state:
                logger.info(f"Signing out from handler: {auth_handler_id}")
                await auth_handler.flow.sign_out(context)

    async def sign_out(
        self,
        context: TurnContext,
        state: TurnState,
        auth_handler_id: Optional[str] = None,
    ) -> None:
        """
        Signs out the current user.
        This method clears the user's token and resets the OAuth state.

        Args:
            context: The context object for the current turn.
            state: The state object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use for sign out.
        """
        if auth_handler_id:
            self.__sign_out(context, state, [auth_handler_id])
        else:
            self.__sign_out(context, state, self._auth_handlers.keys())

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        Args:
            handler: The handler function to call on successful sign-in.
        """
        self.__sign_in_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.
        Args:
            handler: The handler function to call on sign-in failure.
        """
        self.__sign_in_failure = handler
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
import jwt
from typing import Dict, Optional, Callable, Awaitable

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

logger = logging.getLogger(__name__)


class SignInState(StoreItem, BaseModel):
    """
    Interface defining the sign-in state for OAuth flows.
    """

    continuation_activity: Optional[Activity] = None
    handler_id: Optional[str] = None
    completed: Optional[bool] = False

    def store_item_to_json(self) -> dict:
        return self.model_dump(exclude_unset=True)

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "StoreItem":
        return SignInState.model_validate(json_data)


class AuthHandler:
    """
    Interface defining an authorization handler for OAuth flows.
    """

    def __init__(
        self,
        name: str = None,
        title: str = None,
        text: str = None,
        abs_oauth_connection_name: str = None,
        obo_connection_name: str = None,
        **kwargs,
    ):
        """
        Initializes a new instance of AuthHandler.

        Args:
            name: The name of the OAuth connection.
            auto: Whether to automatically start the OAuth flow.
            title: Title for the OAuth card.
            text: Text for the OAuth button.
        """
        self.name = name or kwargs.get("NAME")
        self.title = title or kwargs.get("TITLE")
        self.text = text or kwargs.get("TEXT")
        self.abs_oauth_connection_name = abs_oauth_connection_name or kwargs.get(
            "AZUREBOTOAUTHCONNECTIONNAME"
        )
        self.obo_connection_name = obo_connection_name or kwargs.get(
            "OBOCONNECTIONNAME"
        )
        self.flow: OAuthFlow = None
        logger.debug(
            f"AuthHandler initialized: name={self.name}, title={self.title}, text={self.text} abs_connection_name={self.abs_oauth_connection_name} obo_connection_name={self.obo_connection_name}"
        )


# Type alias for authorization handlers dictionary
AuthorizationHandlers = Dict[str, AuthHandler]


class Authorization:
    """
    Class responsible for managing authorization and OAuth flows.
    """

    SIGN_IN_STATE_KEY = f"{UserState.__name__}.__SIGNIN_STATE_"

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
        if storage is None:
            logger.error("Storage is required for Authorization")
            raise ValueError("Storage is required for Authorization")

        user_state = UserState(storage)
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
        auth_handler = self.resolver_handler(auth_handler_id)
        if auth_handler.flow is None:
            logger.error("OAuth flow is not configured for the auth handler")
            raise ValueError("OAuth flow is not configured for the auth handler")

        return await auth_handler.flow.get_user_token(context)

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
        auth_handler = self.resolver_handler(auth_handler_id)
        if not auth_handler.flow:
            logger.error("OAuth flow is not configured for the auth handler")
            raise ValueError("OAuth flow is not configured for the auth handler")

        token_response = await auth_handler.flow.get_user_token(context)

        if self._is_exchangeable(token_response.token if token_response else None):
            return await self._handle_obo(token_response.token, scopes, auth_handler_id)

        return token_response

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

    def get_flow_state(self, auth_handler_id: Optional[str] = None) -> FlowState:
        """
        Gets the current state of the OAuth flow.

        Args:
            auth_handler_id: Optional ID of the auth handler to check, defaults to first handler.

        Returns:
            The flow state object.
        """
        flow = self.resolver_handler(auth_handler_id).flow
        if flow is None:
            # Return a default FlowState if no flow is configured
            return FlowState()

        # Return flow state if available
        return flow.flow_state or FlowState()

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        turn_state: TurnState,
        auth_handler_id: str,
        sec_route: bool = True,
    ) -> TokenResponse:
        """
        Begins or continues an OAuth flow.

        Args:
            context: The context object for the current turn.
            state: The state object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        auth_handler = self.resolver_handler(auth_handler_id)
        # Get or initialize sign-in state
        sign_in_state = turn_state.get_value(
            self.SIGN_IN_STATE_KEY, target_cls=SignInState
        )
        if sign_in_state is None:
            sign_in_state = SignInState(
                continuation_activity=None, handler_id=None, completed=False
            )

        flow = auth_handler.flow
        if flow is None:
            logger.error("OAuth flow is not configured for the auth handler")
            raise ValueError("OAuth flow is not configured for the auth handler")

        logger.info(
            "Beginning or continuing OAuth flow for handler: %s", auth_handler_id
        )
        token_response = await flow.get_user_token(context)
        if token_response and token_response.token:
            logger.debug("Token obtained successfully")
            return token_response

        # Get the current flow state
        flow_state = await flow._get_flow_state(context)

        if not flow_state.flow_started:
            logger.info("Starting new OAuth flow for handler: %s", auth_handler_id)
            token_response = await flow.begin_flow(context)
            if sec_route:
                sign_in_state.continuation_activity = context.activity
                sign_in_state.handler_id = auth_handler_id
                turn_state.set_value(self.SIGN_IN_STATE_KEY, sign_in_state)
        else:
            logger.info(
                "Continuing existing OAuth flow for handler: %s", auth_handler_id
            )
            token_response = await flow.continue_flow(context)
            # Check if sign-in was successful and call handler if configured
            if token_response and token_response.token:
                if self._sign_in_handler:
                    logger.info("Sign-in successful, calling sign-in handler")
                    await self._sign_in_handler(context, turn_state, auth_handler_id)
                if sec_route:
                    turn_state.delete_value(self.SIGN_IN_STATE_KEY)
            else:
                if self._sign_in_failed_handler:
                    logger.warning(
                        "Sign-in failed, calling sign-in failed handler",
                        stack_info=True,
                    )
                    await self._sign_in_failed_handler(
                        context, turn_state, auth_handler_id
                    )

        await turn_state.save(context)
        return token_response

    def resolver_handler(self, auth_handler_id: Optional[str] = None) -> AuthHandler:
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
        first_key = next(iter(self._auth_handlers))
        return self._auth_handlers[first_key]

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
        if auth_handler_id is None:
            # Sign out from all handlers
            for handler_key, auth_handler in self._auth_handlers.items():
                if auth_handler.flow:
                    logger.info(f"Signing out from handler: {handler_key}")
                    await auth_handler.flow.sign_out(context)
        else:
            # Sign out from specific handler
            auth_handler = self.resolver_handler(auth_handler_id)
            if auth_handler.flow:
                logger.info(f"Signing out from handler: {auth_handler_id}")
                await auth_handler.flow.sign_out(context)

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        Args:
            handler: The handler function to call on successful sign-in.
        """
        self._sign_in_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.
        Args:
            handler: The handler function to call on sign-in failure.
        """
        self._sign_in_failed_handler = handler

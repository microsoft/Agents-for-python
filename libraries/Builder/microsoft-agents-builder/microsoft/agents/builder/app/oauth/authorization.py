# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import os
from typing import Dict, Optional, Callable, Awaitable, Protocol

from microsoft.agents.storage import Storage
from microsoft.agents.core.models import TokenResponse

from ...turn_context import TurnContext
from ...app.state.turn_state import TurnState
from ...oauth_flow import OAuthFlow
from ...state.user_state import UserState


class AuthHandler(Protocol):
    """
    Interface defining an authorization handler for OAuth flows.
    """

    name: Optional[str] = None
    auto: Optional[bool] = None
    flow: Optional[OAuthFlow] = None
    title: Optional[str] = None
    text: Optional[str] = None


# Type alias for authorization handlers dictionary
AuthorizationHandlers = Dict[str, AuthHandler]


class Authorization:
    """
    Class responsible for managing authorization and OAuth flows.
    """

    def __init__(self, storage: Storage, auth_handlers: AuthorizationHandlers):
        """
        Creates a new instance of Authorization.

        Args:
            storage: The storage system to use for state management.
            auth_handlers: Configuration for OAuth providers.

        Raises:
            ValueError: If storage is None or no auth handlers are provided.
        """
        if storage is None:
            raise ValueError("Storage is required for Authorization")

        user_state = UserState(storage)

        if not auth_handlers or len(auth_handlers) == 0:
            raise ValueError("The authorization does not have any auth handlers")

        self._auth_handlers = auth_handlers
        self._sign_in_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None

        # Configure each auth handler
        for handler_key, auth_handler in self._auth_handlers.items():
            # Set connection name from environment if not provided
            if (
                auth_handler.name is None
                and os.getenv(f"{handler_key}_connectionName") is None
            ):
                raise ValueError(
                    f"AuthHandler name {handler_key}_connectionName not set in authorization "
                    f"and not found in env vars."
                )

            # Set properties from environment variables if not already set
            auth_handler.name = auth_handler.name or os.getenv(
                f"{handler_key}_connectionName"
            )
            auth_handler.title = auth_handler.title or os.getenv(
                f"{handler_key}_connectionTitle"
            )
            auth_handler.text = auth_handler.text or os.getenv(
                f"{handler_key}_connectionText"
            )
            auth_handler.auto = (
                auth_handler.auto
                if auth_handler.auto is not None
                else os.getenv(f"{handler_key}_connectionAuto") == "true"
            )

            # Create OAuth flow with configuration
            messages_config = {}
            if auth_handler.title:
                messages_config["card_title"] = auth_handler.title
            if auth_handler.text:
                messages_config["button_text"] = auth_handler.text

            auth_handler.flow = OAuthFlow(
                user_state=user_state,
                connection_name=auth_handler.name,
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
            raise ValueError("OAuth flow is not configured for the auth handler")

        return await auth_handler.flow.get_user_token(context)

    def get_flow_state(self, auth_handler_id: Optional[str] = None) -> bool:
        """
        Gets the current state of the OAuth flow.

        Args:
            auth_handler_id: Optional ID of the auth handler to check, defaults to first handler.

        Returns:
            Whether the flow has started.
        """
        flow = self.resolver_handler(auth_handler_id).flow
        if flow is None:
            return False

        # Return flow state if available
        return flow.state.flow_started if flow.state else False

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        state: TurnState,
        auth_handler_id: Optional[str] = None,
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
        flow = self.resolver_handler(auth_handler_id).flow
        if flow is None:
            raise ValueError("OAuth flow is not configured for the auth handler")

        # Get the current flow state
        flow_state = await flow._get_user_state(context)

        if not flow_state.flow_started:
            token_response = await flow.begin_flow(context)
        else:
            token_response = await flow.continue_flow(context)
            # Check if sign-in was successful and call handler if configured
            if token_response and token_response.token and self._sign_in_handler:
                await self._sign_in_handler(context, state, auth_handler_id)

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
                    await auth_handler.flow.sign_out(context)
        else:
            # Sign out from specific handler
            auth_handler = self.resolver_handler(auth_handler_id)
            if auth_handler.flow:
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

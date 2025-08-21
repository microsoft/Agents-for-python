# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
import jwt
from typing import Dict, Optional, Callable, Awaitable
from collections.abc import Iterable
from contextlib import asynccontextmanager

from microsoft.agents.hosting.core.authorization import (
    Connections,
    AccessTokenProviderBase,
)
from microsoft.agents.hosting.core.storage import Storage
from microsoft.agents.activity import TokenResponse, Activity
from microsoft.agents.hosting.core.storage import StoreItem
from microsoft.agents.hosting.core.connector.client import UserTokenClient
from pydantic import BaseModel

from ...turn_context import TurnContext
from ...app.state.turn_state import TurnState
# from ...oauth_flow import AuthFlow
from ...state.user_state import UserState
from .auth_handler import AuthHandler

from .models import FlowResponse, FlowState, FlowStateTag, FlowErrorTag
from .flow_storage_client import FlowStorageClient
from .auth_flow import AuthFlow

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
        auth_handlers: dict[str, AuthHandler] = None,
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
        # if not auth_handlers:
        #     raise ValueError("At least one AuthHandler must be provided")

        # user_state = UserState(storage)

        self.__storage = storage
        self.__connection_manager = connection_manager

        auth_configuration: Dict = kwargs.get("AGENTAPPLICATION", {}).get(
            "USERAUTHORIZATION", {}
        )

        # self.__auto_signin = (
        #     auto_signin
        #     if auto_signin is not None
        #     else auth_configuration.get("AUTOSIGNIN", False)
        # )

        handlers_config: Dict[str, Dict] = auth_configuration.get("HANDLERS")
        if not auth_handlers and handlers_config:
            auth_handlers = {
                handler_name: AuthHandler(
                    name=handler_name, **config.get("SETTINGS", {})
                )
                for handler_name, config in handlers_config.items()
            }

        self.__auth_handlers = auth_handlers or {}
        self.__sign_in_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None
        self.__sign_in_failed_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None

        # # Configure each auth handler
        # for auth_handler in self.__auth_handlers.values():
        #     # Create OAuth flow with configuration
        #     messages_config = {}
        #     if auth_handler.title:
        #         messages_config["card_title"] = auth_handler.title
        #     if auth_handler.text:
        #         messages_config["button_text"] = auth_handler.text

        #     logger.debug(f"Configuring OAuth flow for handler: {auth_handler.name}")
        #     auth_handler.flow = AuthFlow(
        #         storage=storage,
        #         abs_oauth_connection_name=auth_handler.abs_oauth_connection_name,
        #         messages_configuration=messages_config if messages_config else None,
        #     )

    def __check_for_ids(self, context: TurnContext):
        """Checks for IDs necessary to load a new or existing flow."""
        if (
            not context.activity.channel_id or
            not context.activity.from_property or
            not context.activity.from_property.id
        ):
            raise ValueError("Channel ID and User ID are required")

    async def __load_flow(self, context: TurnContext, auth_handler_id: str) -> tuple[AuthFlow, FlowStorageClient, FlowState]:
        """Loads the OAuth flow for a specific auth handler.

        Args:
            context: The context object for the current turn.
            auth_handler_id: The ID of the auth handler to use.

        Returns:
            The AuthFlow returned corresponds to the flow associated with the
            chosen handler, and the channel and user info found in the context.

            The FlowStorageClient corresponds to the channel and user info.
            The FlowState returned is the flow state for the given channel/user/handler
            triple at the time of creating the flow.
        """
        user_token_client: UserTokenClient = context.turn_state.get(context.adapter.USER_TOKEN_CLIENT_KEY) # robrandao: TODO
        auth_handler: AuthHandler = self.resolve_handler(auth_handler_id)
        
        self.__check_for_ids(context)
        channel_id = context.activity.channel_id
        user_id = context.activity.from_property.id

        flow_storage_client = FlowStorageClient(channel_id, user_id, self.__storage)
        flow_state: FlowState = await flow_storage_client.read(auth_handler_id)

        if not flow_state:
            flow_state = FlowState(
                channel_id=channel_id,
                user_id=user_id,
                auth_handler_id=auth_handler_id,
                abs_oauth_connection_name=auth_handler.abs_oauth_connection_name
            )

        flow = AuthFlow(flow_state, user_token_client)
        return flow, flow_storage_client, flow_state

    @asynccontextmanager
    async def open_flow(self, context: TurnContext, auth_handler_id: str) -> AuthFlow:
        """Loads an Auth flow and saves changes the changes to storage if any are made.

        Args:
            context: The context object for the current turn.
            auth_handler_id: ID of the auth handler to use.

        Yields:
            AuthFlow:
                The AuthFlow instance loaded from storage or newly created
                if not yet present in storage.
        """
        if not context or not auth_handler_id:
            raise ValueError("context and auth_handler_id are required")
    
        flow, flow_storage_client, init_flow_state = self.__load_flow(context, auth_handler_id)
        yield flow

        new_flow_state = flow.flow_state
        if new_flow_state != init_flow_state:
            flow_storage_client.write(new_flow_state)

    async def get_token(
        self, context: TurnContext, auth_handler_id: str
    ) -> TokenResponse:
        """
        Gets the token for a specific auth handler.

        Args:
            context: The context object for the current turn.
  auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        async with self.open_flow(context, auth_handler_id) as flow:
            return await flow.get_user_token(context)

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
        async with self.open_flow(context, auth_handler_id) as flow:
            token_response = await flow.get_user_token()

        if token_response and self.__is_exchangeable(token_response.token):
            return await self.__handle_obo(token_response.token, scopes, auth_handler_id)

        return TokenResponse()

        # auth_handler = self.resolver_handler(auth_handler_id)
        # if not auth_handler.flow:
        #     logger.error("OAuth flow is not configured for the auth handler")
        #     raise ValueError("OAuth flow is not configured for the auth handler")

        # token_response = await auth_handler.flow.get_user_token(context)

        # if self.__is_exchangeable(token_response.token if token_response else None):
        #     return await self.__handle_obo(token_response.token, scopes, auth_handler_id)

        # return token_response

    def __is_exchangeable(self, token: Optional[str]) -> bool:
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

    async def __handle_obo(
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
        if not self.__connection_manager:
            logger.error("Connection manager is not configured", stack_info=True)
            raise ValueError("Connection manager is not configured")

        auth_handler = self.resolver_handler(handler_id)
        if auth_handler.flow is None:
            logger.error("OAuth flow is not configured for the auth handler")
            raise ValueError("OAuth flow is not configured for the auth handler")

        # Use the flow's OBO method to exchange the token
        token_provider: AccessTokenProviderBase = (
            self.__connection_manager.get_connection(auth_handler.obo_connection_name)
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

    async def get_active_flow_state(self, context: TurnContext) -> Optional[FlowState]:
        """Gets the first active flow state for the current context."""
        flow_storage_client = FlowStorageClient(context, self.__storage)
        for auth_handler_id in self.__auth_handlers.keys():
            flow_state = await flow_storage_client.read(auth_handler_id)
            if flow_state.is_active():
                return flow_state
        return None

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        turn_state: TurnState,
        auth_handler_id: str,
        sec_route: bool = True,
    ) -> FlowResponse:
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

        async with self.open_flow(context, auth_handler_id) as flow:
            flow_response: FlowResponse = await flow.begin_or_continue_flow(context)
        
        flow_state: FlowState = flow_response.flow_state

        if flow_state.tag == FlowStateTag.COMPLETE:
            self.__sign_in_success_handler(context, turn_state, flow_state.handler.id)
        elif flow_state.tag == FlowStateTag.FAILURE:
            self.__sign_in_failure_handler(context, turn_state, flow_state.handler.id, err)
            
        return flow_response

    def resolve_handler(self, auth_handler_id: Optional[str] = None) -> AuthHandler:
        """
        Resolves the auth handler to use based on the provided ID.

        Args:
            auth_handler_id: Optional ID of the auth handler to resolve, defaults to first handler.

        Returns:
            The resolved auth handler.
        """
        if auth_handler_id:
            if auth_handler_id not in self.__auth_handlers:
                logger.error(f"Auth handler '{auth_handler_id}' not found")
                raise ValueError(f"Auth handler '{auth_handler_id}' not found")
            return self.__auth_handlers[auth_handler_id]

        # Return the first handler if no ID specified
        return next(iter(self.__auth_handlers.values))
    
    async def __sign_out(
        self,
        context: TurnContext,
        auth_handler_ids: Iterable[str],
    ) -> None:
        """Signs out from the specified auth handlers.
        
        Args:
            context: The context object for the current turn.
            auth_handler_ids: List of auth handler IDs to sign out from.

        Deletes the associated flow states from storage.
        """
        for auth_handler_id in auth_handler_ids:
            flow, flow_storage_client, initial_flow_state = self.__load_flow(context, auth_handler_id)
            if initial_flow_state:
                logger.info(f"Signing out from handler: {auth_handler_id}")
                await flow.sign_out()
                flow_storage_client.delete(auth_handler_id)

    async def sign_out(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None,
    ) -> None:
        """
        Signs out the current user.
        This method clears the user's token and resets the OAuth state.

        Args:
            context: The context object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use for sign out. If None,
                signs out from all the handlers.

        Deletes the associated flow state(s) from storage.
        """
        if auth_handler_id:
            self.__sign_out(context, [auth_handler_id])
        else:
            self.__sign_out(context, self.__auth_handlers.keys())

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        Args:
            handler: The handler function to call on successful sign-in.
        """
        self.__sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.
        Args:
            handler: The handler function to call on sign-in failure.
        """
        self.__sign_in_failure_handler = handler
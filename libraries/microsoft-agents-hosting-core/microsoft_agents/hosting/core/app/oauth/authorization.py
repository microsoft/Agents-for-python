# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
import jwt
from typing import Dict, Optional, Callable, Awaitable, AsyncIterator
from collections.abc import Iterable
from contextlib import asynccontextmanager

from microsoft_agents.hosting.core.authorization import (
    Connections,
    AccessTokenProviderBase,
)
from microsoft_agents.hosting.core.storage import Storage, MemoryStorage
from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core.connector.client import UserTokenClient

from ...turn_context import TurnContext
from ...oauth import OAuthFlow, FlowResponse, FlowState, FlowStateTag, FlowStorageClient
from ..state.turn_state import TurnState
from .auth_handler import AuthHandler

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

        auth_configuration: Dict = kwargs.get("AGENTAPPLICATION", {}).get(
            "USERAUTHORIZATION", {}
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
        self._sign_in_success_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = lambda *args: None
        self._sign_in_failure_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = lambda *args: None

    def _ids_from_context(self, context: TurnContext) -> tuple[str, str]:
        """Checks and returns IDs necessary to load a new or existing flow.

        Raises a ValueError if channel ID or user ID are missing.
        """
        if (
            not context.activity.channel_id
            or not context.activity.from_property
            or not context.activity.from_property.id
        ):
            raise ValueError("Channel ID and User ID are required")

        return context.activity.channel_id, context.activity.from_property.id

    async def _load_flow(
        self, context: TurnContext, auth_handler_id: str = ""
    ) -> tuple[OAuthFlow, FlowStorageClient]:
        """Loads the OAuth flow for a specific auth handler.

        Args:
            context: The context object for the current turn.
            auth_handler_id: The ID of the auth handler to use.

        Returns:
            The OAuthFlow returned corresponds to the flow associated with the
            chosen handler, and the channel and user info found in the context.
            The FlowStorageClient corresponds to the same channel and user info.
        """
        user_token_client: UserTokenClient = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        # resolve handler id
        auth_handler: AuthHandler = self.resolve_handler(auth_handler_id)
        auth_handler_id = auth_handler.name

        channel_id, user_id = self._ids_from_context(context)

        ms_app_id = context.turn_state.get(context.adapter.AGENT_IDENTITY_KEY).claims[
            "aud"
        ]

        # try to load existing state
        flow_storage_client = FlowStorageClient(channel_id, user_id, self._storage)
        logger.info("Loading OAuth flow state from storage")
        flow_state: FlowState = await flow_storage_client.read(auth_handler_id)

        if not flow_state:
            logger.info("No existing flow state found, creating new flow state")
            flow_state = FlowState(
                channel_id=channel_id,
                user_id=user_id,
                auth_handler_id=auth_handler_id,
                connection=auth_handler.abs_oauth_connection_name,
                ms_app_id=ms_app_id,
            )
            await flow_storage_client.write(flow_state)

        flow = OAuthFlow(flow_state, user_token_client)
        return flow, flow_storage_client

    @asynccontextmanager
    async def open_flow(
        self, context: TurnContext, auth_handler_id: str = ""
    ) -> AsyncIterator[OAuthFlow]:
        """Loads an OAuth flow and saves changes the changes to storage if any are made.

        Args:
            context: The context object for the current turn.
            auth_handler_id: ID of the auth handler to use.
                If none provided, uses the first handler.

        Yields:
            OAuthFlow:
                The OAuthFlow instance loaded from storage or newly created
                if not yet present in storage.
        """
        if not context:
            logger.error("No context provided to open_flow")
            raise ValueError("context is required")

        flow, flow_storage_client = await self._load_flow(context, auth_handler_id)
        yield flow
        logger.info("Saving OAuth flow state to storage")
        await flow_storage_client.write(flow.flow_state)

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
        logger.info("Getting token for auth handler: %s", auth_handler_id)
        async with self.open_flow(context, auth_handler_id) as flow:
            return await flow.get_user_token()

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
        logger.info("Exchanging token for scopes: %s", scopes)
        async with self.open_flow(context, auth_handler_id) as flow:
            token_response = await flow.get_user_token()

        if token_response and self._is_exchangeable(token_response.token):
            logger.debug("Token is exchangeable, performing OBO flow")
            return await self._handle_obo(token_response.token, scopes, auth_handler_id)

        return TokenResponse()

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
        return TokenResponse(
            token=new_token,
            scopes=scopes,  # Expiration can be set based on the token provider's response
        )

    async def get_active_flow_state(self, context: TurnContext) -> Optional[FlowState]:
        """Gets the first active flow state for the current context."""
        logger.debug("Getting active flow state")
        channel_id, user_id = self._ids_from_context(context)
        flow_storage_client = FlowStorageClient(channel_id, user_id, self._storage)
        for auth_handler_id in self._auth_handlers.keys():
            flow_state = await flow_storage_client.read(auth_handler_id)
            if flow_state and flow_state.is_active():
                return flow_state
        return None

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        turn_state: TurnState,
        auth_handler_id: str = "",
    ) -> FlowResponse:
        """Begins or continues an OAuth flow.

        Args:
            context: The context object for the current turn.
            turn_state: The state object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.

        """
        if not auth_handler_id:
            auth_handler_id = self.resolve_handler().name

        logger.debug("Beginning or continuing OAuth flow")
        async with self.open_flow(context, auth_handler_id) as flow:
            prev_tag = flow.flow_state.tag
            flow_response: FlowResponse = await flow.begin_or_continue_flow(
                context.activity
            )

        flow_state: FlowState = flow_response.flow_state

        if (
            flow_state.tag == FlowStateTag.COMPLETE
            and prev_tag != FlowStateTag.COMPLETE
        ):
            logger.debug("Calling Authorization sign in success handler")
            self._sign_in_success_handler(
                context, turn_state, flow_state.auth_handler_id
            )
        elif flow_state.tag == FlowStateTag.FAILURE:
            logger.debug("Calling Authorization sign in failure handler")
            self._sign_in_failure_handler(
                context,
                turn_state,
                flow_state.auth_handler_id,
                flow_response.flow_error_tag,
            )

        return flow_response

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

    async def _sign_out(
        self,
        context: TurnContext,
        auth_handler_ids: Iterable[str],
    ) -> None:
        """Signs out from the specified auth handlers.

        Args:
            context: The context object for the current turn.
            auth_handler_ids: Iterable of auth handler IDs to sign out from.

        Deletes the associated flow states from storage.
        """
        for auth_handler_id in auth_handler_ids:
            flow, flow_storage_client = await self._load_flow(context, auth_handler_id)
            # ensure that the id is valid
            self.resolve_handler(auth_handler_id)
            logger.info("Signing out from handler: %s", auth_handler_id)
            await flow.sign_out()
            await flow_storage_client.delete(auth_handler_id)

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
            await self._sign_out(context, [auth_handler_id])
        else:
            await self._sign_out(context, self._auth_handlers.keys())

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        Args:
            handler: The handler function to call on successful sign-in.
        """
        self._sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.
        Args:
            handler: The handler function to call on sign-in failure.
        """
        self._sign_in_failure_handler = handler

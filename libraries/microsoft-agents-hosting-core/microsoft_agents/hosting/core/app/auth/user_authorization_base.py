# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
from abc import ABC
from re import U
from typing import Dict, Optional, Callable, Awaitable, AsyncIterator, TypeVar
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
from .authorization_variant import AuthorizationVariant
from .auth_handler import AuthHandler

logger = logging.getLogger(__name__)

class UserAuthorizationBase(AuthorizationVariant, ABC):
    """
    Class responsible for managing authorization and OAuth flows.
    Handles multiple OAuth providers and manages the complete authentication lifecycle.
    """
    
    async def _load_flow(
        self, context: TurnContext, auth_handler_id: str
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
        auth_handler: AuthHandler = self._auth_handlers[auth_handler_id]
        auth_handler_id = auth_handler.name

        if (
            not context.activity.channel_id
            or not context.activity.from_property
            or not context.activity.from_property.id
        ):
            raise ValueError("Channel ID and User ID are required")

        channel_id = context.activity.channel_id
        user_id = context.activity.from_property.id

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

    async def begin_or_continue_flow(
        self,
        context: TurnContext,
        auth_handler_id: str
    ) -> FlowResponse:
        """Begins or continues an OAuth flow.

        Args:
            context: The context object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.

        """

        logger.debug("Beginning or continuing OAuth flow")

        flow, flow_storage_client = await self._load_flow(context, auth_handler_id)
        flow_response: FlowResponse = await flow.begin_or_continue_flow(context.activity)

        logger.info("Saving OAuth flow state to storage")
        await flow_storage_client.write(flow_response.flow_state)

        return flow_response

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
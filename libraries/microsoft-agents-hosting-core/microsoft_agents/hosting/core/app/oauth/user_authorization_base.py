# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import logging
from abc import ABC
from typing import Optional
from collections.abc import Iterable

from microsoft_agents.hosting.core.connector.client import UserTokenClient

from ...turn_context import TurnContext
from ...oauth import OAuthFlow, FlowResponse, FlowState, FlowStorageClient
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

        A new flow is created in Storage if none exists for the channel, user, and handler
        combination.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to use.
        :type auth_handler_id: str
        :return: A tuple containing the OAuthFlow and FlowStorageClient created from the
            context and the specified auth handler.
        :rtype: tuple[OAuthFlow, FlowStorageClient]
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
        self, context: TurnContext, auth_handler_id: str
    ) -> FlowResponse:
        """Begins or continues an OAuth flow.

        Delegates to the OAuthFlow to handle the activity and manage the flow state.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to use.
        :type auth_handler_id: str
        :return: The FlowResponse from the OAuth flow.
        :rtype: FlowResponse
        """

        logger.debug("Beginning or continuing OAuth flow")

        flow, flow_storage_client = await self._load_flow(context, auth_handler_id)
        # prev_tag = flow.flow_state.tag
        flow_response: FlowResponse = await flow.begin_or_continue_flow(
            context.activity
        )

        logger.info("Saving OAuth flow state to storage")
        await flow_storage_client.write(flow_response.flow_state)

        # optimization for the future. Would like to double check this logic.
        # if prev_tag != flow_response.flow_state.tag and flow_response.flow_state.tag == FlowStateTag.COMPLETE:
        #     # Clear the flow state on completion
        #     await flow_storage_client.delete(auth_handler_id)

        return flow_response

    async def _sign_out(
        self,
        context: TurnContext,
        auth_handler_ids: Iterable[str],
    ) -> None:
        """Signs out from the specified auth handlers.

        Deletes the associated flows from storage.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param auth_handler_ids: Iterable of auth handler IDs to sign out from.
        :type auth_handler_ids: Iterable[str]
        :return: None
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

        :param context: The context object for the current turn.
        :param auth_handler_id: Optional ID of the auth handler to use for sign out. If None,
            signs out from all the handlers.
        """
        if auth_handler_id:
            await self._sign_out(context, [auth_handler_id])
        else:
            await self._sign_out(context, self._auth_handlers.keys())

"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging
import jwt
from typing import Optional

from microsoft_agents.activity import (
    Attachment,
    ActionTypes,
    CardAction,
    OAuthCard,
    TokenResponse,
)

from microsoft_agents.hosting.core.card_factory import CardFactory
from microsoft_agents.hosting.core.message_factory import MessageFactory
from microsoft_agents.hosting.core.connector.client import UserTokenClient
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core._oauth import (
    _OAuthFlow,
    _FlowResponse,
    _FlowState,
    _FlowStorageClient,
    _FlowStateTag,
)
from .._sign_in_response import _SignInResponse
from ._authorization_handler import _AuthorizationHandler

logger = logging.getLogger(__name__)


class _UserAuthorization(_AuthorizationHandler):
    """
    Class responsible for managing authorization and OAuth flows.
    Handles multiple OAuth providers and manages the complete authentication lifecycle.
    """

    async def _load_flow(
        self, context: TurnContext
    ) -> tuple[_OAuthFlow, _FlowStorageClient]:
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
        flow_storage_client = _FlowStorageClient(channel_id, user_id, self._storage)
        logger.info("Loading OAuth flow state from storage")
        flow_state: _FlowState = await flow_storage_client.read(self._id)
        if not flow_state:
            logger.info("No existing flow state found, creating new flow state")
            flow_state = _FlowState(
                channel_id=channel_id,
                user_id=user_id,
                auth_handler_id=self._id,
                connection=self._handler.abs_oauth_connection_name,
                ms_app_id=ms_app_id,
            )
            # await flow_storage_client.write(flow_state)

        flow = _OAuthFlow(flow_state, user_token_client)
        return flow, flow_storage_client

    async def _handle_obo(
        self,
        context: TurnContext,
        input_token_response: TokenResponse,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
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
        if not input_token_response:
            return input_token_response

        token = input_token_response.token

        connection_name = exchange_connection or self._handler.obo_connection_name
        exchange_scopes = exchange_scopes or self._handler.scopes

        if not connection_name or not exchange_scopes:
            return input_token_response

        if not input_token_response.is_exchangeable():
            return input_token_response

        token_provider = self._connection_manager.get_connection(connection_name)
        if not token_provider:
            raise ValueError(f"Connection '{connection_name}' not found")

        token = await token_provider.acquire_token_on_behalf_of(
            scopes=exchange_scopes,
            user_assertion=input_token_response.token,
        )
        return TokenResponse(token=token) if token else TokenResponse()

    async def _sign_out(
        self,
        context: TurnContext,
    ) -> None:
        """
        _Signs out the current user.
        This method clears the user's token and resets the OAuth state.

        :param context: The context object for the current turn.
        :param auth_handler_id: Optional ID of the auth handler to use for sign out. If None,
            signs out from all the handlers.
        """
        flow, flow_storage_client = await self._load_flow(context)
        logger.info("Signing out from handler: %s", self._id)
        await flow.sign_out()
        await flow_storage_client.delete(self._id)

    async def _handle_flow_response(
        self, context: TurnContext, flow_response: _FlowResponse
    ) -> None:
        """Handles CONTINUE and FAILURE flow responses, sending activities back."""
        flow_state: _FlowState = flow_response.flow_state

        if flow_state.tag == _FlowStateTag.BEGIN:
            # Create the OAuth card
            sign_in_resource = flow_response.sign_in_resource
            assert sign_in_resource
            o_card: Attachment = CardFactory.oauth_card(
                OAuthCard(
                    text="Sign in",
                    connection_name=flow_state.connection,
                    buttons=[
                        CardAction(
                            title="Sign in",
                            type=ActionTypes.signin,
                            value=sign_in_resource.sign_in_link,
                            channel_data=None,
                        )
                    ],
                    token_exchange_resource=sign_in_resource.token_exchange_resource,
                    token_post_resource=sign_in_resource.token_post_resource,
                )
            )
            # Send the card to the user
            await context.send_activity(MessageFactory.attachment(o_card))
        elif flow_state.tag == _FlowStateTag.FAILURE:
            if flow_state.reached_max_attempts():
                await context.send_activity(
                    MessageFactory.text(
                        "Sign-in failed. Max retries reached. Please try again later."
                    )
                )
            elif flow_state.is_expired():
                await context.send_activity(
                    MessageFactory.text("Sign-in session expired. Please try again.")
                )
            else:
                logger.warning("Sign-in flow failed for unknown reasons.")
                await context.send_activity("Sign-in failed. Please try again.")

    async def _sign_in(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> _SignInResponse:
        """Begins or continues an OAuth flow.

        Handles the flow response, sending the OAuth card to the context.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to use.
        :type auth_handler_id: str
        :return: The _SignInResponse containing the token response and flow state tag.
        :rtype: _SignInResponse
        """
        flow, flow_storage_client = await self._load_flow(context)
        flow_response: _FlowResponse = await flow.begin_or_continue_flow(
            context.activity
        )

        logger.info("Saving OAuth flow state to storage")
        await flow_storage_client.write(flow_response.flow_state)
        await self._handle_flow_response(context, flow_response)

        if flow_response.token_response:
            # attempt exchange if needed
            # if not needed, returns the same token
            token_response = await self._handle_obo(
                context,
                flow_response.token_response,
                exchange_connection,
                exchange_scopes,
            )

            return _SignInResponse(
                token_response=token_response,
                tag=_FlowStateTag.COMPLETE if token_response else _FlowStateTag.FAILURE,
            )

        return _SignInResponse(tag=flow_response.flow_state.tag)

    async def get_refreshed_token(
        self,
        context: TurnContext,
        exchange_connection: Optional[str] = None,
        exchange_scopes: Optional[list[str]] = None,
    ) -> TokenResponse:
        """Attempts to get a refreshed token for the user with the given scopes

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param exchange_connection: Optional name of the connection to use for token exchange. If None, default connection will be used.
        :type exchange_connection: Optional[str], Optional
        :param exchange_scopes: Optional list of scopes to request during token exchange. If None, default scopes will be used.
        :type exchange_scopes: Optional[list[str]], Optional
        """
        flow, _ = await self._load_flow(context)
        input_token_response = await flow.get_user_token()
        return await self._handle_obo(
            context,
            input_token_response,
            exchange_connection,
            exchange_scopes,
        )

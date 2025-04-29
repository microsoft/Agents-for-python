# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import base64
from datetime import datetime
import json

from microsoft.agents.connector.client import UserTokenClient
from microsoft.agents.core.models import (
    ActionTypes,
    ActivityTypes,
    CardAction,
    Attachment,
    OAuthCard,
    TokenExchangeState,
    TokenResponse,
)
from microsoft.agents.core import (
    TurnContextProtocol as TurnContext,
)
from microsoft.agents.storage import StoreItem
from pydantic import BaseModel

from .message_factory import MessageFactory
from .card_factory import CardFactory
from .state.state_property_accessor import StatePropertyAccessor
from .state.user_state import UserState


class FlowState(StoreItem, BaseModel):
    flow_started: bool = False
    user_token: str = ""
    flow_expires: float = 0

    def store_item_to_json(self) -> dict:
        return self.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "StoreItem":
        return FlowState.model_validate(json_data)


class OAuthFlow:
    """
    Manages the OAuth flow for Web Chat.
    """

    def __init__(
        self, user_state: UserState, connection_name: str, app_id: str, **kwargs
    ):
        """
        Creates a new instance of OAuthFlow.
        :param user_state: The user state.
        """
        if not connection_name:
            raise ValueError(
                "OAuthFlow.__init__: connectionName expected but not found"
            )
        if not app_id:
            raise ValueError(
                "OAuthFlow.__init__: appId expected but not found. Ensure the appId is set in your environment variables."
            )

        self.connection_name = connection_name
        self.app_id = app_id
        self.state: FlowState | None = None
        self.flow_state_accessor: StatePropertyAccessor = user_state.create_property(
            "flowState"
        )

    async def get_user_token(self, context: TurnContext) -> TokenResponse:
        token_client: UserTokenClient = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        return await token_client.user_token.get_token(
            user_id=context.activity.from_property.id,
            connection_name=self.connection_name,
            channel_id=context.activity.channel_id,
        )

    async def begin_flow(self, context: TurnContext) -> TokenResponse:
        """
        Starts the OAuth flow.

        :param context: The turn context.
        :return: A TokenResponse object.
        """
        # logger.info('Starting OAuth flow')
        self.state = await self._get_user_state(context)

        if not self.connection_name:
            raise ValueError(
                "connectionName is not set in the auth config, review your environment variables"
            )

        # Get token client from turn state
        token_client: UserTokenClient = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        # Try to get existing token
        user_token = await token_client.user_token.get_token(
            user_id=context.activity.from_property.id,
            connection_name=self.connection_name,
            channel_id=context.activity.channel_id,
        )

        if user_token and user_token.token:
            # Already have token, return it
            self.state.flow_started = False
            self.state.flow_expires = 0
            await self.flow_state_accessor.set(context, self.state)
            # logger.info('User token retrieved successfully from service')
            return user_token

        # No token, need to start sign-in flow
        token_exchange_state = TokenExchangeState(
            connection_name=self.connection_name,
            conversation=context.activity.get_conversation_reference(),
            relates_to=context.activity.relates_to,
            ms_app_id=self.app_id,
        )
        serialized_state = base64.b64encode(
            json.dumps(
                token_exchange_state.model_dump(
                    by_alias=True, exclude_none=True, exclude_unset=True
                )
            ).encode(encoding="UTF-8", errors="strict")
        ).decode()

        signing_resource = await token_client.agent_sign_in.get_sign_in_resource(
            state=serialized_state,
        )

        # Create the OAuth card
        o_card: Attachment = CardFactory.oauth_card(
            OAuthCard(
                text="Sign in",
                connection_name=self.connection_name,
                buttons=[
                    CardAction(
                        title="Sign in",
                        type=ActionTypes.signin,
                        value=signing_resource.sign_in_link,
                    )
                ],
                token_exchange_resource=signing_resource.token_exchange_resource,
                token_post_resource=signing_resource.token_post_resource,
            )
        )

        # Send the card to the user
        await context.send_activity(MessageFactory.attachment(o_card))

        # Update flow state
        self.state.flow_started = True
        self.state.flow_expires = datetime.now().timestamp() + 30000
        await self.flow_state_accessor.set(context, self.state)
        # logger.info('OAuth begin flow completed, waiting for user to sign in')

        # Return in-progress response
        return TokenResponse()

    async def continue_flow(self, context: TurnContext) -> TokenResponse:
        """
        Continues the OAuth flow.
        :param context: The turn context.
        :return: A TokenResponse object.
        """
        self.state = await self._get_user_state(context)

        if (
            self.state.flow_expires != 0
            and datetime.now().timestamp() > self.state.flow_expires
        ):
            # logger.warn("Flow expired")
            self.state.flow_started = False
            await context.send_activity(
                MessageFactory.text("Sign-in session expired. Please try again.")
            )
            return TokenResponse()

        cont_flow_activity = context.activity

        # Handle message type activities (typically when the user enters a code)
        if cont_flow_activity.type == ActivityTypes.message:
            magic_code = cont_flow_activity.text

            # Get token client from turn state
            token_client: UserTokenClient = context.turn_state.get(
                context.adapter.USER_TOKEN_CLIENT_KEY
            )

            # Try to get token with the code
            result = await token_client.user_token.get_token(
                user_id=cont_flow_activity.from_property.id,
                connection_name=self.connection_name,
                channel_id=cont_flow_activity.channel_id,
                code=magic_code,
            )

            if result:
                token_response = TokenResponse.model_validate(result)
                if token_response.token:
                    self.state.flow_started = False
                    self.state.user_token = token_response.token
                    await self.flow_state_accessor.set(context, self.state)
                return token_response
            return TokenResponse()

        # Handle verify state invoke activity
        if (
            cont_flow_activity.type == ActivityTypes.invoke
            and cont_flow_activity.name == "signin/verifyState"
        ):
            # logger.info('Continuing OAuth flow with verifyState')
            token_verify_state = cont_flow_activity.value
            magic_code = token_verify_state.get("state")

            # Get token client from turn state
            token_client: UserTokenClient = context.turn_state.get(
                context.adapter.USER_TOKEN_CLIENT_KEY
            )

            # Try to get token with the code
            result = await token_client.user_token.get_token(
                user_id=cont_flow_activity.from_property.id,
                connection_name=self.connection_name,
                channel_id=cont_flow_activity.channel_id,
                code=magic_code,
            )

            if result:
                token_response = TokenResponse.model_validate(result)
                if token_response.token:
                    self.state.flow_started = False
                    self.state.user_token = token_response.token
                    await self.flow_state_accessor.set(context, self.state)
                return token_response
            return TokenResponse()

        # Handle token exchange invoke activity
        if (
            cont_flow_activity.type == ActivityTypes.invoke
            and cont_flow_activity.name == "signin/tokenExchange"
        ):
            # logger.info('Continuing OAuth flow with tokenExchange')
            token_exchange_request = cont_flow_activity.value

            # Dedupe checks to prevent duplicate processing
            token_exchange_id = token_exchange_request.get("id")
            if (
                hasattr(self, "token_exchange_id")
                and self.token_exchange_id == token_exchange_id
            ):
                # Already processed this request
                return TokenResponse()

            # Store this request ID
            self.token_exchange_id = token_exchange_id

            # Get token client from turn state
            token_client: UserTokenClient = context.turn_state.get(
                context.adapter.USER_TOKEN_CLIENT_KEY
            )

            # Exchange the token
            user_token_resp = await token_client.user_token.exchange_token(
                user_id=cont_flow_activity.from_property.id,
                connection_name=self.connection_name,
                channel_id=cont_flow_activity.channel_id,
                body=token_exchange_request,
            )

            if user_token_resp and user_token_resp.token:
                # logger.info('Token exchanged')
                self.state.flow_started = False
                self.state.user_token = user_token_resp.token
                await self.flow_state_accessor.set(context, self.state)
                return user_token_resp
            else:
                # logger.warn('Token exchange failed')
                self.state.flow_started = True
                await self.flow_state_accessor.set(context, self.state)
                return TokenResponse()

        return TokenResponse()

    async def sign_out(self, context: TurnContext):
        """
        Signs the user out.
        :param context: The turn context.
        """
        token_client: UserTokenClient = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        await token_client.user_token.sign_out(
            user_id=context.activity.from_property.id,
            connection_name=self.connection_name,
            channel_id=context.activity.channel_id,
        )
        self.state.flow_started = False
        self.state.user_token = ""
        self.state.flow_expires = 0
        await self.flow_state_accessor.set(context, self.state)
        # logger.info("User signed out successfully")

    async def _get_user_state(self, context: TurnContext) -> FlowState:
        """
        Gets the user state.
        :param context: The turn context.
        :return: The user state.
        """
        user_profile: FlowState | None = await self.flow_state_accessor.get(
            context, target_cls=FlowState
        )
        if user_profile is None:
            user_profile = FlowState()
        return user_profile

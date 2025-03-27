# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft.agents.core.models import Attachment
from microsoft.agents.connector import UserTokenClient
from microsoft.agents.builder.cards.card_factory import CardFactory
from microsoft.agents.core.turn_context_protocol import (
    TurnContextProtocol as TurnContext,
)
from microsoft.agents.builder.message_factory import MessageFactory

from .channel_service_adapter import ChannelServiceAdapter
from .state.state_property_accessor import StatePropertyAccessor
from .state.user_state import UserState


class FlowState:
    def __init__(self):
        self.flow_started = False
        self.user_token = ""
        self.flow_expires = 0


class BasicOAuthFlow:
    """
    Manages the OAuth flow for Web Chat.
    """

    def __init__(self, user_state: UserState):
        """
        Creates a new instance of BasicOAuthFlow.
        :param user_state: The user state.
        """
        self.user_token_client: UserTokenClient = None
        self.state: FlowState | None = None
        self.flow_state_accessor: StatePropertyAccessor = user_state.create_property(
            "flowState"
        )

    async def get_oauth_token(self, context: TurnContext) -> str:
        """
        Gets the OAuth token.
        :param context: The turn context.
        :return: The user token.
        """
        self.state = await self.get_user_state(context)
        if self.state.user_token:
            return self.state.user_token

        if self.state.flow_expires and self.state.flow_expires < context.adapter.now():
            # logger.warn("Sign-in flow expired")
            self.state.flow_started = False
            self.state.user_token = ""
            await context.send_activity(
                MessageFactory.text("Sign-in session expired. Please try again.")
            )

        ret_val = ""
        auth_config = context.adapter.auth_config
        if not auth_config.connection_name:
            raise ValueError(
                "connectionName is not set in the auth config, review your environment variables"
            )

        self.user_token_client = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        if self.state.flow_started:
            user_token = await self.user_token_client.get_user_token(
                auth_config.connection_name,
                context.activity.channel_id,
                context.activity.from_property.id,
            )
            if user_token:
                # logger.info("Token obtained")
                self.state.user_token = user_token.token
                self.state.flow_started = False
            else:
                code = context.activity.text
                user_token = await self.user_token_client.get_user_token(
                    auth_config.connection_name,
                    context.activity.channel_id,
                    context.activity.from_property.id,
                    code,
                )
                if user_token:
                    # logger.info("Token obtained with code")
                    self.state.user_token = user_token.token
                    self.state.flow_started = False
                else:
                    # logger.error("Sign in failed")
                    await context.send_activity(MessageFactory.text("Sign in failed"))
            ret_val = self.state.user_token
        else:
            signing_resource = await self.user_token_client.get_sign_in_resource(
                auth_config.client_id, auth_config.connection_name, context.activity
            )
            o_card: Attachment = CardFactory.oauth_card(
                auth_config.connection_name, "Sign in", "", signing_resource
            )
            await context.send_activity(MessageFactory.attachment(o_card))
            self.state.flow_started = True
            self.state.flow_expires = context.adapter.now() + 30000
            # logger.info("OAuth flow started")

        await self.flow_state_accessor.set(context, self.state)
        return ret_val

    async def sign_out(self, context: TurnContext):
        """
        Signs the user out.
        :param context: The turn context.
        """
        await self.user_token_client.sign_out(
            context.activity.from_property.id,
            context.adapter.auth_config.connection_name,
            context.activity.channel_id,
        )
        self.state.flow_started = False
        self.state.user_token = ""
        self.state.flow_expires = 0
        await self.flow_state_accessor.set(context, self.state)
        logger.info("User signed out successfully")

    async def get_user_state(self, context: TurnContext) -> FlowState:
        """
        Gets the user state.
        :param context: The turn context.
        :return: The user state.
        """
        user_profile: FlowState | None = await self.flow_state_accessor.get(
            context, None
        )
        if user_profile is None:
            user_profile = FlowState()
        return user_profile

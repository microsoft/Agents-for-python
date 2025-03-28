# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime

from microsoft.agents.connector import UserTokenClient
from microsoft.agents.core.models import ActionTypes, CardAction, Attachment, OAuthCard
from microsoft.agents.core import (
    TurnContextProtocol as TurnContext,
)

from .message_factory import MessageFactory
from .card_factory import CardFactory
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

    def __init__(self, user_state: UserState, connection_name: str):
        """
        Creates a new instance of BasicOAuthFlow.
        :param user_state: The user state.
        """
        if not connection_name:
            raise ValueError(
                "BasicOAuthFlow.__init__: connectionName expected but not found"
            )

        self.connection_name = connection_name
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

        if (
            self.state.flow_expires
            and self.state.flow_expires < datetime.now().timestamp()
        ):
            # logger.warn("Sign-in flow expired")
            self.state.flow_started = False
            self.state.user_token = ""
            await context.send_activity(
                MessageFactory.text("Sign-in session expired. Please try again.")
            )

        ret_val = ""
        if not self.connection_name:
            raise ValueError(
                "connectionName is not set in the auth config, review your environment variables"
            )

        # TODO: Fix property discovery
        self.user_token_client = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        if self.state.flow_started:
            user_token = await self.user_token_client.user_token.get_token(
                context.activity.from_property.id,
                self.connection_name,
                context.activity.channel_id,
            )
            if user_token:
                # logger.info("Token obtained")
                self.state.user_token = user_token["token"]
                self.state.flow_started = False
            else:
                code = context.activity.text
                user_token = await self.user_token_client.user_token.get_token(
                    context.activity.from_property.id,
                    self.connection_name,
                    context.activity.channel_id,
                    code,
                )
                if user_token:
                    # logger.info("Token obtained with code")
                    self.state.user_token = user_token["token"]
                    self.state.flow_started = False
                else:
                    # logger.error("Sign in failed")
                    await context.send_activity(MessageFactory.text("Sign in failed"))
            ret_val = self.state.user_token
        else:
            signing_resource = (
                await self.user_token_client.agent_sign_in.get_sign_in_resource(
                    context.activity.from_property.id,
                    self.connection_name,
                    context.activity,
                )
            )
            # TODO: move this to CardFactory
            o_card: Attachment = CardFactory.oauth_card(
                OAuthCard(
                    text="Sign in",
                    connection_name=self.connection_name,
                    buttons=[
                        CardAction(
                            title="Sign in",
                            text="",
                            type=ActionTypes.signin,
                            value=signing_resource.sign_in_link,
                        )
                    ],
                    token_exchange_resource=signing_resource.token_exchange_resource,
                ),
                self.connection_name,
                "Sign in",
                "",
                signing_resource,
            )
            await context.send_activity(MessageFactory.attachment(o_card))
            self.state.flow_started = True
            self.state.flow_expires = datetime.now().timestamp() + 30000
            # logger.info("OAuth flow started")

        await self.flow_state_accessor.set(context, self.state)
        return ret_val

    async def sign_out(self, context: TurnContext):
        """
        Signs the user out.
        :param context: The turn context.
        """
        await self.user_token_client.user_token.sign_out(
            context.activity.from_property.id,
            self.connection_name,
            context.activity.channel_id,
        )
        self.state.flow_started = False
        self.state.user_token = ""
        self.state.flow_expires = 0
        await self.flow_state_accessor.set(context, self.state)
        # logger.info("User signed out successfully")

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

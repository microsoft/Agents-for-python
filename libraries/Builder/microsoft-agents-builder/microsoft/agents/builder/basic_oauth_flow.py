# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import base64
from datetime import datetime
import json

from microsoft.agents.connector import UserTokenClient
from microsoft.agents.core.models import (
    ActionTypes,
    CardAction,
    Attachment,
    OAuthCard,
    SignInResource,
    TokenExchangeState,
)
from microsoft.agents.core import (
    TurnContextProtocol as TurnContext,
)
from microsoft.agents.storage import StoreItem
from pydantic import BaseModel, ConfigDict

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


class BasicOAuthFlow:
    """
    Manages the OAuth flow for Web Chat.
    """

    def __init__(self, user_state: UserState, connection_name: str, app_id: str):
        """
        Creates a new instance of BasicOAuthFlow.
        :param user_state: The user state.
        """
        if not connection_name:
            raise ValueError(
                "BasicOAuthFlow.__init__: connectionName expected but not found"
            )
        if not app_id:
            raise ValueError(
                "BasicOAuthFlow.__init__: appId expected but not found. Ensure the appId is set in your environment variables."
            )

        self.connection_name = connection_name
        self.app_id = app_id
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
        token_client: UserTokenClient = context.turn_state.get(
            context.adapter.USER_TOKEN_CLIENT_KEY
        )

        if self.state.flow_started:
            user_token = await token_client.user_token.get_token(
                user_id=context.activity.from_property.id,
                connection_name=self.connection_name,
                channel_id=context.activity.channel_id,
            )
            if user_token:
                # logger.info("Token obtained")
                self.state.user_token = user_token["token"]
                self.state.flow_started = False
            else:
                code = context.activity.text
                user_token = await token_client.user_token.get_token(
                    user_id=context.activity.from_property.id,
                    connection_name=self.connection_name,
                    channel_id=context.activity.channel_id,
                    code=code,
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
            token_exchange_state = TokenExchangeState(
                connection_name=self.connection_name,
                conversation=context.activity.get_conversation_reference(),
                relates_to=context.activity.relates_to,
                ms_app_id=self.app_id,
            )
            serialized_state = base64.b64encode(
                json.dumps(token_exchange_state.model_dump(by_alias=True)).encode(
                    encoding="UTF-8", errors="strict"
                )
            ).decode()
            token_client_response = (
                await token_client.agent_sign_in.get_sign_in_resource(
                    state=serialized_state,
                )
            )
            signing_resource = SignInResource.model_validate(token_client_response)
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
                )
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

    async def get_user_state(self, context: TurnContext) -> FlowState:
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

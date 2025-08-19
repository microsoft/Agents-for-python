# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging

from enum import Enum
from datetime import datetime
from typing import Dict, Optional

from microsoft.agents.hosting.core.connector.client import UserTokenClient
from microsoft.agents.activity import (
    ActivityTypes,
    TokenExchangeState,
    TokenResponse,
)
from microsoft.agents.activity import (
    TurnContextProtocol as TurnContext,
)
from microsoft.agents.hosting.core.storage import StoreItem, Storage
from pydantic import BaseModel, PositiveInt

from .message_factory import MessageFactory
from .card_factory import CardFactory
from .models import FlowResponse, FlowState, FlowStateTag, FlowErrorTag

logger = logging.getLogger(__name__)


class AuthFlow:
    """
    Manages the OAuth flow.

    This class is responsible for managing the entire OAuth flow, including
    obtaining user tokens, signing out users, and handling token exchanges.

    Contract with other classes (usage of other classes is enforced in unit tests):
        TurnContext.activity.channel_id
        TurnContext.activity.from_property.id

        UserTokenClient: user_token.get_token(), user_token.sign_out()
    """

    def __init__(
        self,
        abs_oauth_connection_name: str,
        user_token_client: UserTokenClient,
        flow_state: FlowState = None,
        **kwargs
    ):
        """
        Arguments:
            abs_oauth_connection_name: 

            user_token_client:

            flow_state: 
        """
        if not abs_oauth_connection_name:
            raise ValueError(
                "OAuthFlow.__init__: abs_oauth_connection_name required."
            )
        if not user_token_client:
            raise ValueError(
                "OAuthFlow.__init__: user_token_client required."
            )
        
        flow_state = flow_state or FlowState() # robrandao: TODO
        self.flow_state = flow_state.copy()
        self.__abs_oauth_connection_name = abs_oauth_connection_name
        self.__user_token_client = user_token_client

    # async def __initialize_token_client(self, context: TurnContext) -> None:
    #     # robrandao: TODO is this safe
    #     # use cached value later
    #     self.__user_token_client = context.turn_state.get(context.adapter.USER_TOKEN_CLIENT_KEY)

    async def __get_ids_or_raise(self, context: TurnContext) -> TokenResponse:
        if (
            not not context.activity.channel_id or
            not context.activity.from_property or
            not context.activity.from_property.id
        ):
            raise ValueError("User ID or Channel ID is not set in the activity.")
        
        return context.activity.channel_id, context.activity.from_property.id

    async def __get_user_token(self, context: TurnContext, magic_code=None) -> TokenResponse:
        channel_id, from_id = self.__get_ids_or_raise(context)

        return await self.__user_token_client.user_token.get_token(
            user_id=from_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id,
            magic_code=magic_code
        )
    
    async def get_user_token(self, context: TurnContext) -> TokenResponse:
        return self.__get_user_token(context)
    
    async def sign_out(self, context: TurnContext) -> None:
        channel_id, from_id = self.__get_ids_or_raise(context)
        
        return await self.__user_token_client.user_token.sign_out(
            user_id=from_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id
        )
    
    async def __use_attempt(self) -> None:
        if self.flow_state.attempts_remaining <= 0:
            self.flow_state.flow_state_tag = FlowStateTag.FAILURE
    
    async def begin_flow(self, context: TurnContext) -> FlowResponse:

        self.flow_state = FlowState(
            id=self.__abs_oauth_connection_name,
            channel_id=context.activity.channel_id,
            user_id=context.activity.from_property.id
        )

        # init flow state
        
        token_response = self.get_user_token(context)
        if token_response:
            return FlowResponse(
                flow_state=self.flow_state,
                token_response=token_response
            )

        token_exchange_state = TokenExchangeState(
            connection_name=self.__abs_oauth_connection_name,
            conversation=context.activity.get_conversation_reference(),
            relates_to=context.activity.relates_to,
            ms_app_id=context.turn_state.get(context.adapter.AGENT_IDENTITY_KEY).claims["aud"] # robrandao: TODO
        )

        sign_in_resource = await self.__user_token_client.agent_sign_in.get_sign_in_resource(
            state=token_exchange_state.get_encoded_state())

        return FlowResponse(flow_state=self.flow_state, sign_in_resource=sign_in_resource)
    
    async def __continue_from_message(self, context: TurnContext) -> tuple[TokenResponse, FlowErrorTag]:
        magic_code: str = context.activity.text
        if magic_code and magic_code.isdigit() and len(magic_code) == 6:
            token_response: TokenResponse = await self.__get_user_token(context, magic_code)

            if token_response:
                return token_response, FlowErrorTag.NONE
            else:
                return token_response, FlowErrorTag.MAGIC_CODE
        else:
            return TokenResponse(), FlowErrorTag.MAGIC_FORMAT
        
    async def __continue_from_invoke_verify_state(self, context: TurnContext) -> TokenResponse:
        token_verify_state = context.activity.value
        magic_code: str = token_verify_state.get("state")
        token_response: TokenResponse = await self.__get_user_token(context, magic_code)
        return token_response
    
    async def __continue_from_invoke_token_exchange(self, context: TurnContext) -> TokenResponse:
        channel_id, from_id = self.__get_ids_or_raise(context)
        token_exchange_request = context.activity.value
        token_response = await self.__user_token_client.user_token.exchange_token(
            user_id=from_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id,
            body=token_exchange_request
        )
        return token_response, FlowErrorTag.NONE

    async def continue_flow(self, context: TurnContext) -> FlowResponse:
        logger.debug("Continuing auth flow...")

        if not self.flow_state.is_active():
            self.flow_state.flow_state_tag = FlowStateTag.FAILURE
            return FlowResponse(flow_state=self.flow_state)
        
        continue_flow_activity = context.activity

        flow_error_tag = FlowErrorTag.NONE
        if continue_flow_activity.type == ActivityTypes.message:
            token_response, flow_error_tag = await self.__continue_from_message(context)
        elif continue_flow_activity.type == ActivityTypes.invoke and continue_flow_activity.name == "signin/verifyState":
            token_response = await self.__continue_from_invoke_verify_state(context)
        elif continue_flow_activity.flow_error_tag == ActivityTypes.invoke and continue_flow_activity.name == "signin/tokenExchange":
            token_response = await self.__continue_from_invoke_token_exchange(context)
        else:
            pass

        if not token_response and flow_error_tag == FlowErrorTag.NONE:
            flow_error_tag = FlowErrorTag.UNKNOWN

        if flow_error_tag != FlowErrorTag.NONE:
            self.__use_attempt()

        return FlowResponse(
            flow_state=self.flow_state,
            flow_error_tag=flow_error_tag,
            token_response=token_response
        )

    async def begin_or_continue_flow(self, context: TurnContext) -> FlowResponse:
        if self.flow_state.is_active():
            return await self.continue_flow(context)
        else:
            return await self.begin_flow(context)
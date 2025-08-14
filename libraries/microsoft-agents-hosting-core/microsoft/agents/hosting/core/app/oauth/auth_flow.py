# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging

from enum import Enum
from datetime import datetime
from typing import Dict, Optional

from microsoft.agents.hosting.core.connector.client import UserTokenClient
from microsoft.agents.activity import (
    ActionTypes,
    ActivityTypes,
    CardAction,
    Attachment,
    OAuthCard,
    TokenExchangeState,
    TokenResponse,
    Activity,
)
from microsoft.agents.activity import (
    TurnContextProtocol as TurnContext,
)
from microsoft.agents.hosting.core.storage import StoreItem, Storage
from pydantic import BaseModel, PositiveInt

from .message_factory import MessageFactory
from .card_factory import CardFactory
from .models import FlowResponse, FlowState, FlowStateTag

logger = logging.getLogger(__name__)


class AuthFlow:
    """
    Manages the OAuth flow.
    """

    def __init__(
        self,
        flow_state: FlowState = None,
        abs_oauth_connection_name: str = None,
        user_token_client: Optional[UserTokenClient] = None,
        **kwargs
    ):
        if not abs_oauth_connection_name:
            raise ValueError(
                "OAuthFlow.__init__: abs_oauth_connection_name required."
            )
        
        self.flow_state = flow_state or FlowState()
        self.__abs_oauth_connection_name = abs_oauth_connection_name
        self.__user_token_client = user_token_client

    async def __initialize_token_client(self, context: TurnContext) -> None:
        # robrandao: TODO is this safe
        # use cached value later
        self.__user_token_client = context.turn_state.get(context.adapter.USER_TOKEN_CLIENT_KEY)

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
        await self.__initialize_token_client(context)

        return await self.user_token_client.user_token.get_token(
            user_id=from_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id,
            magic_code=magic_code
        )
    
    async def get_user_token(self, context: TurnContext) -> TokenResponse:
        return self.__get_user_token(context)
    
    async def sign_out(self, context: TurnContext) -> None:
        channel_id, from_id = self.__get_ids_or_raise(context)
        await self.__initialize_token_client(context)
        
        return await self.__user_token_client.user_token.get_token(
            user_id=from_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id
        )
    
    async def __use_attempt(self, context: TurnContext) -> None:
        if self.flow_state.attempts_remaining <= 0:
            self.flow_state.flow_state_tag = FlowStateTag.FAILURE

    async def __failed_attempt(self, context: TurnContext) -> None:
        pass
    
    async def begin_flow(self, context: TurnContext) -> FlowResponse:

        # init flow state
        
        token_response = self.get_user_token(context)
        if token_response and token_response.token:
            pass

        token_exchange_state = TokenExchangeState(
            connection_name=self.__abs_oauth_connection_name,
            conversation=context.activity.get_conversation_reference(),
            relates_to=context.activity.relates_to,
            ms_app_id=context.turn_state.get(context.adapter.AGENT_IDENTITY_KEY).claims["aud"] # robrandao: TODO
        )

        sign_in_resource = await self.__user_token_client.agent_sign_in.get_sign_in_resource(state=token_exchange_sate.get_encoded_state())

        return FlowResponse(flow_state=self.flow_state)
    
    async def __continue_from_message(self, context: TurnContext) -> None:

        magic_code = activity.text
        if magic_code and magic_code.isdigit() and len(magic_code) == 6:
            result = self.__get_user_token(context, magic_code)

            if result and result.token:
                return result
            else:
                return InvalidCodeError
        else:
            return InvalidCodeFormatError
        
    async def __continue_from_invoke_verify_state(self, context: TurnContext) -> None:
        token_verify_sate = context.activity.value
        magic_code = token_verify_state.get("state")
        result = self.__get_user_token(context, magic_code)
        if result and result.token:
            pass
        return None
    
    async def __continue_from_invoke_token_exchange(self, context: TurnContext) -> None:
        await self.__initialize_token_client(context)
        channel_id, from_id = self.__get_ids_or_raise(context)

        token_exchange_request = context.activity.value
        token_exchange_id = token_exchange_request.get("id")

        return await self.__user_token_client.user_token.exchange_token(
            user_id=context.activity.from_property.id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=channel_id,
            body=token_exchange_request
        )

    async def continue_flow(self, context: TurnContext) -> FlowResponse:
        if self.flow_state.is_expired() or self.flow_state.reached_max_retries():
            self.flow_state.flow_state_tag = FlowStateTag.FAILURE
            return FlowResponse(flow_state=self.flow_state)
        
        continue_flow_activity = context.activity

        if continue_flow_activity.type == ActivityTypes.message:
            token_response, flow_error = continue_flow_from_message()
        elif continue_flow_activity.type == ActivityTypes.invoke and continue_flow_activity.name == "signin/verifyState":
            token_response, flow_error = continue_flow_from_invoke_verify_state()
        elif continue_flow_activity.type == ActivityTypes.invoke and continue_flow_activity.name == "signin/tokenExchange":
            token_response, flow_error = continue_flow_from_invoke_token_exchange()
        else:
            pass

        if flow_error != FlowError.NONE and token_response and token_response.token:
            pass
        elif flow_error == FlowError.NONE:
            flow_error = 
        
        pass


    async def begin_or_continue_flow(self, context: TurnContext) -> FlowResponse:

        if self.flow_state.is_active():
            return await self.continue_flow(context)
        else:
            return await self.begin_flow(context)
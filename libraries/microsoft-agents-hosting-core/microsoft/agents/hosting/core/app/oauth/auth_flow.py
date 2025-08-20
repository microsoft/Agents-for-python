# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging

from enum import Enum
from datetime import datetime
from typing import Dict, Optional

from microsoft.agents.hosting.core.connector.client import UserTokenClient
from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    TokenExchangeState,
    TokenResponse,
)
from microsoft.agents.hosting.core.storage import StoreItem, Storage
from pydantic import BaseModel, PositiveInt

from .models import FlowResponse, FlowState, FlowStateTag, FlowErrorTag
from .utils import raise_if_empty_or_None

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
        flow_state: FlowState,
        user_token_client: UserTokenClient,
        **kwargs
    ):
        """
        Arguments:
            abs_oauth_connection_name: 

            user_token_client:

            flow_state: 
        """
        raise_if_empty_or_None(
            self.__init__.__name__,
            flow_state=flow_state,
            user_token_client=user_token_client
        )

        if (not flow_state.abs_oauth_connection_name or
            not flow_state.ms_app_id or
            not flow_state.channel_id or
            not flow_state.user_id):
            raise ValueError("OAuthFlow.__init__: flow_state must have ms_app_id, channel_id, user_id, abs_oauth_connection_name defined")
        
        self.__flow_state = flow_state.model_copy()
        self.__abs_oauth_connection_name = self.__flow_state.abs_oauth_connection_name
        self.__ms_app_id = self.__flow_state.ms_app_id
        self.__channel_id = self.__flow_state.channel_id
        self.__user_id = self.__flow_state.user_id

        self.__user_token_client = user_token_client

        self.__flow_duration = kwargs.get("flow_duration", 60000) # defaults to 60 seconds
        self.__max_attempts = kwargs.get("max_attempts", 3) # defaults to 3 max attempts

    @property
    def flow_state(self) -> FlowState:
        return self.__flow_state.model_copy()

    # async def __initialize_token_client(self, context: TurnContext) -> None:
    #     # robrandao: TODO is this safe
    #     # use cached value later
    #     self.__user_token_client = context.turn_state.get(context.adapter.USER_TOKEN_CLIENT_KEY)
    
    async def get_user_token(self, magic_code: str = None) -> TokenResponse:
        """Get the user token based on the context.
        
        Args:
            magic_code (str, optional): Defaults to None. The magic code for user authentication.

        Returns:
            TokenResponse
                The user token response.

        Notes
        -----
        flow_state.user_token is updated with the latest token.

        """
        token_response: TokenResponse = await self.__user_token_client.user_token.get_token(
            user_id=self.__user_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=self.__channel_id,
            magic_code=magic_code
        )
        if token_response:
            self.__flow_state.user_token = token_response.token
        return token_response
    
    async def sign_out(self) -> None:
        """Sign out the user."""
        await self.__user_token_client.user_token.sign_out(
            user_id=self.__user_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=self.__channel_id
        )
        self.__flow_state.user_token = ""
        self.__flow_state.tag = FlowStateTag.NOT_STARTED
    
    def __use_attempt(self) -> None:
        self.__flow_state.attempts_remaining -= 1
        if self.__flow_state.attempts_remaining <= 0:
            self.__flow_state.tag = FlowStateTag.FAILURE
    
    async def begin_flow(self, activity: Activity) -> FlowResponse:

        # init flow state
        
        token_response = await self.get_user_token()
        if token_response:
            return FlowResponse(
                flow_state=self.__flow_state,
                token_response=token_response
            )
        
        self.__flow_state.tag = FlowStateTag.BEGIN
        self.__flow_state.expires_at = datetime.now().timestamp() + self.__flow_duration
        self.__flow_state.attempts_remaining = self.__max_attempts
        self.__flow_state.user_token = ""

        token_exchange_state = TokenExchangeState(
            connection_name=self.__abs_oauth_connection_name,
            conversation=activity.get_conversation_reference(),
            relates_to=activity.relates_to,
            ms_app_id=self.__ms_app_id # robrandao: TODO
        )

        sign_in_resource = await self.__user_token_client.agent_sign_in.get_sign_in_resource(
            state=token_exchange_state.get_encoded_state())

        return FlowResponse(flow_state=self.__flow_state, sign_in_resource=sign_in_resource)
    
    async def __continue_from_message(self, activity: Activity) -> tuple[TokenResponse, FlowErrorTag]:
        magic_code: str = activity.text
        if magic_code and magic_code.isdigit() and len(magic_code) == 6:
            token_response: TokenResponse = await self.get_user_token(magic_code)

            if token_response:
                return token_response, FlowErrorTag.NONE
            else:
                return token_response, FlowErrorTag.MAGIC_CODE_INCORRECT
        else:
            return TokenResponse(), FlowErrorTag.MAGIC_FORMAT
        
    async def __continue_from_invoke_verify_state(self, activity: Activity) -> TokenResponse:
        token_verify_state = activity.value
        magic_code: str = token_verify_state.get("state")
        token_response: TokenResponse = await self.get_user_token(magic_code)
        return token_response
    
    async def __continue_from_invoke_token_exchange(self, activity: Activity) -> TokenResponse:
        token_exchange_request = activity.value
        token_response = await self.__user_token_client.user_token.exchange_token(
            user_id=self.__user_id,
            connection_name=self.__abs_oauth_connection_name,
            channel_id=self.__channel_id,
            body=token_exchange_request
        )
        return token_response

    async def continue_flow(self, activity: Activity) -> FlowResponse:
        logger.debug("Continuing auth flow...")

        if not self.__flow_state.is_active():
            self.__flow_state.tag = FlowStateTag.FAILURE
            return FlowResponse(flow_state=self.__flow_state)

        flow_error_tag = FlowErrorTag.NONE
        if activity.type == ActivityTypes.message:
            token_response, flow_error_tag = await self.__continue_from_message(activity)
        elif (activity.type == ActivityTypes.invoke
                and activity.name == "signin/verifyState"):
            token_response = await self.__continue_from_invoke_verify_state(activity)
        elif (activity.type == ActivityTypes.invoke
                and activity.name == "signin/tokenExchange"):
            token_response = await self.__continue_from_invoke_token_exchange(activity)
        else:
            raise ValueError("Unknown activity type")

        if not token_response and flow_error_tag == FlowErrorTag.NONE:
            flow_error_tag = FlowErrorTag.OTHER

        if flow_error_tag != FlowErrorTag.NONE:
            self.__flow_state.tag = FlowStateTag.CONTINUE
            self.__use_attempt()
        else:
            self.__flow_state.tag = FlowStateTag.COMPLETE
            self.__flow_state.expires_at = datetime.now().timestamp() + self.__flow_duration
            self.__flow_state.user_token = token_response.token
            

        return FlowResponse(
            flow_state=self.__flow_state.model_copy(),
            flow_error_tag=flow_error_tag,
            token_response=token_response
        )

    async def begin_or_continue_flow(self, activity: Activity) -> FlowResponse:
        if self.__flow_state.is_active():
            return await self.continue_flow(activity)
        else:
            return await self.begin_flow(activity)
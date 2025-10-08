# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging

from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    TokenExchangeState,
    TokenResponse,
    SignInResource,
)

from ..connector.client import UserTokenClient
from ._flow_state import _FlowState, _FlowStateTag, _FlowErrorTag

logger = logging.getLogger(__name__)


class _FlowResponse(BaseModel):
    """Represents the response for a flow operation."""

    flow_state: _FlowState = _FlowState()
    flow_error_tag: _FlowErrorTag = _FlowErrorTag.NONE
    token_response: Optional[TokenResponse] = None
    sign_in_resource: Optional[SignInResource] = None


class _OAuthFlow:
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
        self, flow_state: _FlowState, user_token_client: UserTokenClient, **kwargs
    ):
        """
        Arguments:
            flow_state: The state of the flow.
            user_token_client: The user token client to use for token operations.

        Keyword Arguments:
            flow_duration: The duration of the flow in milliseconds (default: 60000).
            max_attempts: The maximum number of attempts for the flow
                set when starting a flow (default: 3).
        """
        if not flow_state or not user_token_client:
            raise ValueError(
                "OAuthFlow.__init__(): flow_state and user_token_client are required"
            )

        if (
            not flow_state.connection
            or not flow_state.ms_app_id
            or not flow_state.channel_id
            or not flow_state.user_id
        ):
            raise ValueError(
                "OAuthFlow.__init__: flow_state must have ms_app_id, channel_id, user_id, connection defined"
            )

        logger.debug("Initializing OAuthFlow with flow state: %s", flow_state)

        self._flow_state = flow_state.model_copy()

        self._abs_oauth_connection_name = self._flow_state.connection
        self._ms_app_id = self._flow_state.ms_app_id
        self._channel_id = self._flow_state.channel_id
        self._user_id = self._flow_state.user_id

        self._user_token_client = user_token_client

        self._default_flow_duration = kwargs.get(
            "default_flow_duration", 10 * 60
        )  # default to 10 minutes
        self._max_attempts = kwargs.get("max_attempts", 3)  # defaults to 3 max attempts

        logger.debug(
            "OAuthFlow initialized with connection: %s, ms_app_id: %s, channel_id: %s, user_id: %s",
            self._abs_oauth_connection_name,
            self._ms_app_id,
            self._channel_id,
            self._user_id,
        )
        logger.debug(
            "Default flow duration: %d ms, Max attempts: %d",
            self._default_flow_duration,
            self._max_attempts,
        )

    @property
    def flow_state(self) -> _FlowState:
        return self._flow_state.model_copy()

    async def get_user_token(self, magic_code: str = None) -> TokenResponse:
        """Get the user token based on the context.

        Args:
            magic_code (str, Optional): Defaults to None. The magic code for user authentication.

        Returns:
            TokenResponse
                The user token response.

        Notes:
            flow_state.user_token is updated with the latest token.
        """
        logger.info(
            "Getting user token for user_id: %s, connection: %s",
            self._user_id,
            self._abs_oauth_connection_name,
        )
        token_response: TokenResponse = (
            await self._user_token_client.user_token.get_token(
                user_id=self._user_id,
                connection_name=self._abs_oauth_connection_name,
                channel_id=self._channel_id,
                code=magic_code,
            )
        )
        if token_response:
            logger.info("User token obtained successfully: %s", token_response)
            self._flow_state.expiration = (
                datetime.now(timezone.utc).timestamp() + self._default_flow_duration
            )
            self._flow_state.tag = _FlowStateTag.COMPLETE

        return token_response

    async def sign_out(self) -> None:
        """Sign out the user.

        Sets the flow state tag to NOT_STARTED
        Resets the flow state user_token field
        """
        logger.info(
            "Signing out user_id: %s from connection: %s",
            self._user_id,
            self._abs_oauth_connection_name,
        )
        await self._user_token_client.user_token.sign_out(
            user_id=self._user_id,
            connection_name=self._abs_oauth_connection_name,
            channel_id=self._channel_id,
        )
        self._flow_state.tag = _FlowStateTag.NOT_STARTED

    def _use_attempt(self) -> None:
        """Decrements the remaining attempts for the flow, checking for failure."""
        self._flow_state.attempts_remaining -= 1
        if self._flow_state.attempts_remaining <= 0:
            self._flow_state.tag = _FlowStateTag.FAILURE
        logger.debug(
            "Using an attempt for the OAuth flow. Attempts remaining after use: %d",
            self._flow_state.attempts_remaining,
        )

    async def begin_flow(self, activity: Activity) -> _FlowResponse:
        """Begins the OAuthFlow.

        Args:
            activity: The activity that initiated the flow.

        Returns:
            The response containing the flow state and sign-in resource if applicable.

        Notes:
            The flow state is reset if a token is not obtained from cache.
        """

        logger.debug("Starting new OAuth flow")

        token_exchange_state = TokenExchangeState(
            connection_name=self._abs_oauth_connection_name,
            conversation=activity.get_conversation_reference(),
            relates_to=activity.relates_to,
            ms_app_id=self._ms_app_id,
        )

        res = await self._user_token_client.user_token._get_token_or_sign_in_resource(
            activity.from_property.id,
            self._abs_oauth_connection_name,
            activity.channel_id,
            token_exchange_state.get_encoded_state(),
        )

        if res.token_response:
            logger.info("Skipping flow, user token obtained.")
            self._flow_state.tag = _FlowStateTag.COMPLETE
            self._flow_state.expiration = (
                datetime.now(timezone.utc).timestamp() + self._default_flow_duration
            )
            return _FlowResponse(
                flow_state=self._flow_state, token_response=res.token_response
            )

        self._flow_state.tag = _FlowStateTag.BEGIN
        self._flow_state.expiration = (
            datetime.now(timezone.utc).timestamp() + self._default_flow_duration
        )
        self._flow_state.attempts_remaining = self._max_attempts

        logger.debug("Sign-in resource obtained successfully: %s", res.sign_in_resource)

        return _FlowResponse(
            flow_state=self._flow_state, sign_in_resource=res.sign_in_resource
        )

    async def _continue_from_message(
        self, activity: Activity
    ) -> tuple[TokenResponse, _FlowErrorTag]:
        """Handles the continuation of the flow from a message activity."""
        magic_code: str = activity.text
        if magic_code and magic_code.isdigit() and len(magic_code) == 6:
            token_response: TokenResponse = await self.get_user_token(magic_code)

            if token_response:
                return token_response, _FlowErrorTag.NONE
            else:
                return token_response, _FlowErrorTag.MAGIC_CODE_INCORRECT
        else:
            return TokenResponse(), _FlowErrorTag.MAGIC_FORMAT

    async def _continue_from_invoke_verify_state(
        self, activity: Activity
    ) -> TokenResponse:
        """Handles the continuation of the flow from an invoke activity for verifying state."""
        token_verify_state = activity.value
        magic_code: str = token_verify_state.get("state")
        token_response: TokenResponse = await self.get_user_token(magic_code)
        return token_response

    async def _continue_from_invoke_token_exchange(
        self, activity: Activity
    ) -> TokenResponse:
        """Handles the continuation of the flow from an invoke activity for token exchange."""
        token_exchange_request = activity.value
        token_response = await self._user_token_client.user_token.exchange_token(
            user_id=self._user_id,
            connection_name=self._abs_oauth_connection_name,
            channel_id=self._channel_id,
            body=token_exchange_request,
        )
        return token_response

    async def continue_flow(self, activity: Activity) -> _FlowResponse:
        """Continues the OAuth flow based on the incoming activity.

        Args:
            activity: The incoming activity to continue the flow with.

        Returns:
            A FlowResponse object containing the updated flow state and any token response.

        """
        logger.debug("Continuing auth flow...")

        if not self._flow_state.is_active():
            logger.debug("OAuth flow is not active, cannot continue")
            self._flow_state.tag = _FlowStateTag.FAILURE
            return _FlowResponse(
                flow_state=self._flow_state.model_copy(), token_response=None
            )

        flow_error_tag = _FlowErrorTag.NONE
        if activity.type == ActivityTypes.message:
            token_response, flow_error_tag = await self._continue_from_message(activity)
        elif (
            activity.type == ActivityTypes.invoke
            and activity.name == "signin/verifyState"
        ):
            token_response = await self._continue_from_invoke_verify_state(activity)
        elif (
            activity.type == ActivityTypes.invoke
            and activity.name == "signin/tokenExchange"
        ):
            token_response = await self._continue_from_invoke_token_exchange(activity)
        else:
            raise ValueError(f"Unknown activity type {activity.type}")

        if not token_response and flow_error_tag == _FlowErrorTag.NONE:
            flow_error_tag = _FlowErrorTag.OTHER

        if flow_error_tag != _FlowErrorTag.NONE:
            logger.debug("Flow error occurred: %s", flow_error_tag)
            self._flow_state.tag = _FlowStateTag.CONTINUE
            self._use_attempt()
        else:
            self._flow_state.tag = _FlowStateTag.COMPLETE
            self._flow_state.expiration = (
                datetime.now(timezone.utc).timestamp() + self._default_flow_duration
            )
            logger.debug(
                "OAuth flow completed successfully, got TokenResponse: %s",
                token_response,
            )

        return _FlowResponse(
            flow_state=self._flow_state.model_copy(),
            flow_error_tag=flow_error_tag,
            token_response=token_response,
        )

    async def begin_or_continue_flow(self, activity: Activity) -> _FlowResponse:
        """Begins a new OAuth flow or continues an existing one based on the activity.

        Args:
            activity: The incoming activity to begin or continue the flow with.

        Returns:
            A FlowResponse object containing the updated flow state and any token response.
        """
        self._flow_state.refresh()

        if self._flow_state.is_active():
            logger.debug("Active flow, continuing...")
            return await self.continue_flow(activity)

        logger.debug("No active flow, beginning new flow...")
        return await self.begin_flow(activity)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from datetime import datetime
from typing import Optional

from microsoft.agents.connector.client import UserTokenClient
from microsoft.agents.core.models import (
    ActionTypes,
    ActivityTypes,
    CardAction,
    Attachment,
    OAuthCard,
    TokenExchangeState,
    TokenResponse,
    Activity,
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
    abs_oauth_connection_name: Optional[str] = None
    continuation_activity: Optional[Activity] = None

    def store_item_to_json(self) -> dict:
        return self.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "StoreItem":
        return FlowState.model_validate(json_data)


class OAuthFlow:
    """
    Manages the OAuth flow.
    """

    def __init__(
        self,
        user_state: UserState,
        abs_oauth_connection_name: str,
        user_token_client: Optional[UserTokenClient] = None,
        messages_configuration: dict[str, str] = None,
        **kwargs,
    ):
        """
        Creates a new instance of OAuthFlow.

        Args:
            user_state: The user state.
            abs_oauth_connection_name: The OAuth connection name.
            user_token_client: Optional user token client.
            messages_configuration: Optional messages configuration for backward compatibility.
        """
        if not abs_oauth_connection_name:
            raise ValueError(
                "OAuthFlow.__init__: connectionName expected but not found"
            )

        # Handle backward compatibility with messages_configuration
        self.messages_configuration = messages_configuration or {}

        # Initialize properties
        self.abs_oauth_connection_name = abs_oauth_connection_name
        self.user_token_client = user_token_client
        self.token_exchange_id: Optional[str] = None

        # Initialize state and flow state accessor
        self.state: FlowState | None = None
        self.flow_state_accessor: StatePropertyAccessor = user_state.create_property(
            "flowState"
        )

    async def get_user_token(self, context: TurnContext) -> TokenResponse:
        """
        Retrieves the user token from the user token service.

        Args:
            context: The turn context containing the activity information.

        Returns:
            The user token response.

        Raises:
            ValueError: If the channelId or from properties are not set in the activity.
        """
        await self._initialize_token_client(context)

        if not context.activity.from_property:
            raise ValueError("User ID is not set in the activity.")

        if not context.activity.channel_id:
            raise ValueError("Channel ID is not set in the activity.")

        return await self.user_token_client.user_token.get_token(
            user_id=context.activity.from_property.id,
            connection_name=self.abs_oauth_connection_name,
            channel_id=context.activity.channel_id,
        )

    async def begin_flow(self, context: TurnContext) -> TokenResponse:
        """
        Begins the OAuth flow.

        Args:
            context: The turn context.

        Returns:
            A TokenResponse object.
        """
        self.state = FlowState()

        if not self.abs_oauth_connection_name:
            raise ValueError("connectionName is not set")

        await self._initialize_token_client(context)

        activity = context.activity

        # Try to get existing token first
        user_token = await self.user_token_client.user_token.get_token(
            user_id=activity.from_property.id,
            connection_name=self.abs_oauth_connection_name,
            channel_id=activity.channel_id,
        )

        if user_token and user_token.token:
            # Already have token, return it
            self.state.flow_started = False
            self.state.flow_expires = 0
            self.state.abs_oauth_connection_name = self.abs_oauth_connection_name
            await self.flow_state_accessor.set(context, self.state)
            return user_token

        # No token, need to start sign-in flow
        token_exchange_state = TokenExchangeState(
            connection_name=self.abs_oauth_connection_name,
            conversation=activity.get_conversation_reference(),
            relates_to=activity.relates_to,
            ms_app_id=context.turn_state.get(context.adapter.AGENT_IDENTITY_KEY).claims[
                "aud"
            ],
        )

        signing_resource = (
            await self.user_token_client.agent_sign_in.get_sign_in_resource(
                state=token_exchange_state.get_encoded_state(),
            )
        )

        # Create the OAuth card
        o_card: Attachment = CardFactory.oauth_card(
            OAuthCard(
                text=self.messages_configuration.get("card_title", "Sign in"),
                connection_name=self.abs_oauth_connection_name,
                buttons=[
                    CardAction(
                        title=self.messages_configuration.get("button_text", "Sign in"),
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
        self.state.abs_oauth_connection_name = self.abs_oauth_connection_name
        await self.flow_state_accessor.set(context, self.state)

        # Return in-progress response
        return TokenResponse()

    async def continue_flow(self, context: TurnContext) -> TokenResponse:
        """
        Continues the OAuth flow.

        Args:
            context: The turn context.

        Returns:
            A TokenResponse object.
        """
        await self._initialize_token_client(context)

        if (
            self.state
            and self.state.flow_expires != 0
            and datetime.now().timestamp() > self.state.flow_expires
        ):
            await context.send_activity(
                MessageFactory.text(
                    self.messages_configuration.get(
                        "session_expired_messages",
                        "Sign-in session expired. Please try again.",
                    )
                )
            )
            return TokenResponse()

        cont_flow_activity = context.activity

        # Handle message type activities (typically when the user enters a code)
        if cont_flow_activity.type == ActivityTypes.message:
            magic_code = cont_flow_activity.text

            # Validate magic code format (6 digits)
            if magic_code and magic_code.isdigit() and len(magic_code) == 6:
                result = await self.user_token_client.user_token.get_token(
                    user_id=cont_flow_activity.from_property.id,
                    connection_name=self.abs_oauth_connection_name,
                    channel_id=cont_flow_activity.channel_id,
                    code=magic_code,
                )

                if result and result.token:
                    self.state.flow_started = False
                    self.state.flow_expires = 0
                    self.state.abs_oauth_connection_name = (
                        self.abs_oauth_connection_name
                    )
                    await self.flow_state_accessor.set(context, self.state)
                    return result
                else:
                    await context.send_activity(
                        MessageFactory.text("Invalid code. Please try again.")
                    )
                    self.state.flow_started = True
                    self.state.flow_expires = datetime.now().timestamp() + 30000
                    await self.flow_state_accessor.set(context, self.state)
                    return TokenResponse()
            else:
                await context.send_activity(
                    MessageFactory.text(
                        "Invalid code format. Please enter a 6-digit code."
                    )
                )
                return TokenResponse()

        # Handle verify state invoke activity
        if (
            cont_flow_activity.type == ActivityTypes.invoke
            and cont_flow_activity.name == "signin/verifyState"
        ):
            token_verify_state = cont_flow_activity.value
            magic_code = token_verify_state.get("state")

            result = await self.user_token_client.user_token.get_token(
                user_id=cont_flow_activity.from_property.id,
                connection_name=self.abs_oauth_connection_name,
                channel_id=cont_flow_activity.channel_id,
                code=magic_code,
            )

            if result and result.token:
                self.state.flow_started = False
                self.state.abs_oauth_connection_name = self.abs_oauth_connection_name
                await self.flow_state_accessor.set(context, self.state)
                return result
            return TokenResponse()

        # Handle token exchange invoke activity
        if (
            cont_flow_activity.type == ActivityTypes.invoke
            and cont_flow_activity.name == "signin/tokenExchange"
        ):
            token_exchange_request = cont_flow_activity.value

            # Dedupe checks to prevent duplicate processing
            token_exchange_id = token_exchange_request.get("id")
            if self.token_exchange_id == token_exchange_id:
                # Already processed this request
                return TokenResponse()

            # Store this request ID
            self.token_exchange_id = token_exchange_id

            # Exchange the token
            user_token_resp = await self.user_token_client.user_token.exchange_token(
                user_id=cont_flow_activity.from_property.id,
                connection_name=self.abs_oauth_connection_name,
                channel_id=cont_flow_activity.channel_id,
                body=token_exchange_request,
            )

            if user_token_resp and user_token_resp.token:
                self.state.flow_started = False
                await self.flow_state_accessor.set(context, self.state)
                return user_token_resp
            else:
                self.state.flow_started = True
                return TokenResponse()

        return TokenResponse()

    async def sign_out(self, context: TurnContext) -> None:
        """
        Signs the user out.

        Args:
            context: The turn context.
        """
        await self._initialize_token_client(context)

        await self.user_token_client.user_token.sign_out(
            user_id=context.activity.from_property.id,
            connection_name=self.abs_oauth_connection_name,
            channel_id=context.activity.channel_id,
        )

        self.state.flow_expires = 0
        await self.flow_state_accessor.set(context, self.state)

    async def _get_user_state(self, context: TurnContext) -> FlowState:
        """
        Gets the user state.

        Args:
            context: The turn context.

        Returns:
            The user state.
        """
        user_profile: FlowState | None = await self.flow_state_accessor.get(
            context, target_cls=FlowState
        )
        if user_profile is None:
            user_profile = FlowState()
        return user_profile

    async def _initialize_token_client(self, context: TurnContext) -> None:
        """
        Initializes the user token client if not already set.

        Args:
            context: The turn context.
        """
        if self.user_token_client is None:
            self.user_token_client = context.turn_state.get(
                context.adapter.USER_TOKEN_CLIENT_KEY
            )

        if self.user_token_client is None:
            raise ValueError("UserTokenClient is not available in turn state")

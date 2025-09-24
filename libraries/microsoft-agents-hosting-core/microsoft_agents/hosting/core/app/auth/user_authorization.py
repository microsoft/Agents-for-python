from __future__ import annotations
import logging
from typing import Dict, Optional, Callable, Awaitable, AsyncIterator, TypeVar
from collections.abc import Iterable
from contextlib import asynccontextmanager

from microsoft_agents.hosting.core.authorization import (
    Connections,
    AccessTokenProviderBase,
)
from microsoft_agents.hosting.core.storage import Storage, MemoryStorage
from microsoft_agents.activity import (
    ActionTypes,
    TokenResponse,
    CardAction,
    OAuthCard,
    Attachment,
    CardFactory,
)
from microsoft_agents.hosting.core.connector.client import UserTokenClient

from ...turn_context import TurnContext
from ...oauth import OAuthFlow, FlowResponse, FlowState, FlowStateTag, FlowStorageClient
from ...message_factory import MessageFactory
from ..state.turn_state import TurnState
from .authorization_variant import AuthorizationClient
from .auth_handler import AuthHandler
from .user_authorization_base import UserAuthorizationBase

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)

class UserAuthorization(UserAuthorizationBase[StateT]):

    async def _handle_flow_response(
        self, context: TurnContext, flow_response: FlowResponse
    ) -> None:
        """Handles CONTINUE and FAILURE flow responses, sending activities back."""
        flow_state: FlowState = flow_response.flow_state

        if flow_state.tag == FlowStateTag.BEGIN:
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
        elif flow_state.tag == FlowStateTag.FAILURE:
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

    async def sign_in(self, context: TurnContext, state: StateT, auth_handler_id: Optional[str] = None) -> bool:
        logger.debug(
            "Beginning or continuing flow for auth handler %s",
            auth_handler_id,
        )
        flow_response: FlowResponse = (
            await self.begin_or_continue_flow(
                context, state, auth_handler_id
            )
        )
        await self._handle_flow_response(context, flow_response)
        logger.debug(
            "Flow response flow_state.tag: %s",
            flow_response.flow_state.tag,
        )
        return flow_response.flow_state.tag == FlowStateTag.COMPLETE
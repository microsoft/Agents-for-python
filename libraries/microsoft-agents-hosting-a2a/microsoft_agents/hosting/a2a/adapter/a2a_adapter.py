import logging
from os import sync
from typing import Awaitable, Callable, cast

from fastapi import Request, Response

from a2a.types import (
    SendMessageConfiguration
)
from a2a.server.request_handlers import RequestHandler
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    CallerIdConstants,
    Channels,
    ConversationParameters,
    ConversationReference,
    InvokeResponse,
    ResourceResponse,
    StreamInfo,
)
from microsoft_agents.hosting.core import (
    AuthenticationConstants,
    ChannelAdapter,
    ClaimsIdentity,
    TurnContext,
    ChannelServiceAdapter,
)
from microsoft_agents.hosting.core.channel_adapter_protocol import ChannelAdapterProtocol

from ..request_handlers import A2ARequestHandler
from ..activity import utils, A2AActivity
from .agent_request_context import AgentRequestContext

logger = logging.getLogger(__name__)

class A2AAdapter(ChannelAdapter, ChannelAdapterProtocol):

    def __init__(self, adapter: ChannelAdapterProtocol):

        self._adapter = adapter
        self._a2a_request_handler = A2ARequestHandler(
            self,
            None,
            None,
        )
        self._context_map: dict[str, AgentRequestContext] = {}

    @property
    def a2a_request_handler(self) -> RequestHandler:
        return self._a2a_request_handler

    async def execute_agent_turn(self, context: RequestContext, event_queue: EventQueue) -> None:

        if not context.message:
            raise ValueError("Context message is required.")
        
        self._context_map[context.request_id] = AgentRequestContext(
            request_id=
            identity=
            event_queue=event_queue,
        )

        activity = A2AActivity.from_message(
            "",
            context.task_id,
            context.message,
        )
            
        await self.process_activity_with_a2a(identity, activity)

    def _create_turn_context(
        self,
        claims_identity: ClaimsIdentity,
        oauth_scope: str | None = None,
        activity: Activity | None = None,
    ) -> TurnContext:
        context = TurnContext(self, activity, claims_identity)
        context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY] = oauth_scope
        context.turn_state[ChannelServiceAdapter.AGENT_IDENTITY_KEY] = claims_identity  # for back-compat
        return context

    async def process_activity_with_a2a(
        self,
        claims_identity: ClaimsIdentity,
        activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
    ) -> InvokeResponse | None:

        if activity.channel_id != Channels.a2a:
            raise ValueError("Activity channel_id must be 'a2a'")

        outgoing_audience: str | None = None

        if claims_identity.is_agent_claim():
            outgoing_audience = claims_identity.get_token_audience()
            activity.caller_id = f"{CallerIdConstants.agent_to_agent_prefix}{claims_identity.get_outgoing_app_id()}"
        else:
            outgoing_audience = AuthenticationConstants.AGENTS_SDK_SCOPE

        # Create a turn context and run the pipeline.
        context = self._create_turn_context(
            claims_identity,
            outgoing_audience,
            activity=activity,
        )
        context = self._create_turn_context(claims_identity, Channels.a2a, activity)

        await self.run_pipeline(context, callback)

    async def send_activities(
        self, context: TurnContext, activities: list[Activity]
    ) -> list[ResourceResponse]:

        await self._a2a_request_handler.

        for activity in activities:

            if activity.channel_id != Channels.a2a:
                continue

            entity = activity.get_streaming_entity()

            if entity is not None:
                await self._on_streaming_response(context, activity, entity)
            elif activity.type == ActivityTypes.message:
                await self._on_message_response(context, activity)
            elif activity.type == ActivityTypes.end_of_conversation:
                await self._on_end_of_conversation_response(context, activity)
            else:
                logger.debug("A2AAdapter: Unhandled Activity Type: %s", activity.type)
        
        return await self._adapter.send_activities(context, activities)

    async def _on_streaming_response(self, context: TurnContext, activity: Activity, entity: StreamInfo):
        pass

    async def _on_message_response(self, context: TurnContext, activity: Activity):
        message = utils.get_incoming_message(context)
        state = utils.get_task_state(activity)
        response = utils.activity_to_message(message.context_id, message.task_id, activity)

        await event_queue

    async def _on_end_of_conversation_response(self, context: TurnContext, activity: Activity):
        pass
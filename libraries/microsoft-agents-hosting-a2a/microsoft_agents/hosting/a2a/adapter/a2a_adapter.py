import logging

from datetime import datetime, timezone
from typing import Awaitable, Callable, cast
from uuid import uuid4

from fastapi import Request, Response

from a2a.types import (
    SendMessageConfiguration,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskState,
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
    EndOfConversationCodes,
    InvokeResponse,
    ResourceResponse,
    StreamInfo,
)
from microsoft_agents.hosting.core import (
    Agent,
    AuthenticationConstants,
    ChannelAdapter,
    ClaimsIdentity,
    TurnContext,
    ChannelServiceAdapter,
)
from microsoft_agents.hosting.core.channel_adapter_protocol import ChannelAdapterProtocol
from microsoft_agents.hosting.core.http._http_request_protocol import HttpRequestProtocol

from ..request_handlers import A2ARequestHandler
from ..activity import utils, A2AActivity
from .agent_request_context import AgentRequestContext

from ..constants import _CLAIMS_IDENTITY_KEY

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

    async def execute_agent_turn(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        if not context.message:
            raise ValueError("Context message is required.")

        identity = context.call_context.state.get(_CLAIMS_IDENTITY_KEY, ClaimsIdentity())
        if not isinstance(identity, ClaimsIdentity):
            raise RuntimeError("Invalid identity in context call state.")

        request_id = str(uuid4())

        activity = A2AActivity.from_message(
            request_id,
            context.task_id,
            context.message,
        )
        activity.request_id = request_id

        self._context_map[request_id] = AgentRequestContext(
            request_id=request_id,
            identity=identity,
            event_queue=event_queue,
        )
            
        await self._process_activity_with_a2a(
            identity,
            activity,
            context,
            event_queue,
        )

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

    async def _process_activity_with_a2a(
        self,
        identity: ClaimsIdentity,
        activity: Activity,
        request_context: RequestContext,
        event_queue: EventQueue,
        callback: Callable[[TurnContext], Awaitable] | None = None,
    ) -> InvokeResponse | None:

        if activity.channel_id != Channels.a2a:
            raise ValueError("Activity channel_id must be 'a2a'")

        outgoing_audience: str | None = None

        if identity.is_agent_claim():
            outgoing_audience = identity.get_token_audience()
            activity.caller_id = f"{CallerIdConstants.agent_to_agent_prefix}{identity.get_outgoing_app_id()}"
        else:
            outgoing_audience = AuthenticationConstants.AGENTS_SDK_SCOPE

        # Create a turn context and run the pipeline.
        context = self._create_turn_context(
            identity,
            outgoing_audience,
            activity=activity,
        )
        context.services.set(RequestContext, request_context)
        context.services.set(EventQueue, event_queue)

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
        message = utils.get_incoming_message(context)
        is_informative = entity.stream_type == "informative"

        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        if is_informative:
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=message.task_id,
                context_id=message.context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_WORKING,
                    timestamp=datetime.now(timezone.utc),
                    message=utils.create_message(message.context_id, message.task_id, activity)
                )
            ))
        else:
            artifact = utils.activity_to_artifact(activity, entity.stream_id)
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=message.task_id,
                context_id=message.context_id,
                artifact=artifact,
                append=False,
                last_chunk=True,
            ))

    async def _on_message_response(self, context: TurnContext, activity: Activity):
        message = utils.get_incoming_message(context)
        state = utils.get_task_state(activity)
        response = utils.create_message(message.context_id, message.task_id, activity)

        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=message.task_id,
            context_id=message.context_id,
            status=TaskStatus(
                state=state,
                timestamp=datetime.now(timezone.utc),
                message=response
            )
        ))

    async def _on_end_of_conversation_response(self, context: TurnContext, activity: Activity):
        message = utils.get_incoming_message(context)
        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        if isinstance(activity.value, dict):
            artifact = utils.create_artifact_from_data(
                activity.value,
                name="Result",
                description="Task completion result",
                media_type="application/json"
            )
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=message.task_id,
                context_id=message.context_id,
                artifact=artifact,
                append=False,
                last_chunk=True,
            ))

        task_state: TaskState
        if activity.code == EndOfConversationCodes.error:
            task_state = TaskState.TASK_STATE_FAILED
        elif activity.code == EndOfConversationCodes.user_cancelled:
            task_state = TaskState.TASK_STATE_CANCELED
        else:
            task_state = TaskState.TASK_STATE_COMPLETED

        status_message: Activity
        if utils.has_message_content(activity):
            status_message = activity.model_copy()
            status_message.value = None

        response = utils.create_message(
            message.context_id,
            message.task_id,
            status_message,
        )

        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=message.task_id,
            context_id=message.context_id,
            status=TaskStatus(
                state=task_state,
                timestamp=datetime.now(timezone.utc),
                message=response
            )
        ))
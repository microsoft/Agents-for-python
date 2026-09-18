import logging

from datetime import datetime, timezone
from typing import Awaitable, Callable, cast
from uuid import uuid4

from fastapi import Request, Response

from a2a.types import (
    AgentCard,
    SendMessageConfiguration,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskState,
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
)
from a2a.server.request_handlers import RequestHandler
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskStore, InMemoryTaskStore

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

    def __init__(self, agent: Agent, task_store: TaskStore | None = None):
        """Initializes the A2AAdapter with the given agent and optional task store.
        
        :param agent: The agent instance to be used by the adapter.
        :param task_store: Optional task store for managing tasks. If not provided, an in-memory task store will be used.
        """

        self._agent = agent
        self._a2a_request_handler = A2ARequestHandler(
            self,
            task_store or InMemoryTaskStore(),
            agent_card = self._get_agent_card(),
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

        await self.run_pipeline(context, self._agent.on_turn)

    async def send_activities(
        self, context: TurnContext, activities: list[Activity]
    ) -> list[ResourceResponse]:

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

        return []
        
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

    def _get_agent_card(self) -> AgentCard:

        agent_card = AgentCard(
            name=self._agent_card_name,
            description=self._agent_card_description,
            version=self._agent_card_version,
            security_schemes={
                "jwt": SecurityScheme(http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="bearer"))
            },
            default_input_modes=["application/json"],
            default_output_modes=["application/json"],
            skills=[],
            capabilities=AgentCapabilities(
                extended_agent_card=True,
                streaming=True,
            ),
            supported_interfaces=[],
        )

        agent_interfaces = []
        if not agent_interfaces:
            agent_card.supported_interfaces.append(
                AgentInterface(
                    protocol_binding=TransportProtocol.JSONRPC,
                    url=f"{request.url.scheme}://{request.url.hostname}{path_prefix}/",
                    protocol_version="1.0",
                )
            )
        else:
            for agent_interface in agent_interfaces:
                if agent_interface.protocol in (TransportProtocol.JSONRPC, TransportProtocol.HTTP_JSON):
                    agent_card.supported_interfaces.append(
                        protocol_binding=agent_interface.protocol,
                        url=f"{request.url.scheme}://{request.url.hostname}{path_prefix}/",
                        protocol_version="1.0",
                    )
                else:
                    logger.info("Unsupported protocol: %s", agent_interface.protocol)

        skills = []
        if skills:
            for skill_info in skills:
                agent_card.skills.append(AgentSkill(
                    id=skill_info.id,
                    name=skill_info.name,
                    description=skill_info.description,
                    tags=skill_info.tags,
                    examples=skill_info.examples,
                    input_modes=skill_info.input_modes,
                    output_modes=skill_info.output_modes,
                ))

    def _update_agent_card(self) -> None:
        agent_card = self._get_agent_card()
        self._a2a_request_handler.update_agent_card(agent_card)


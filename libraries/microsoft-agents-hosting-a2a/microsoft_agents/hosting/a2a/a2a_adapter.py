# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from a2a.types import (
    AgentCard,
    AgentInterface,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskState,
    AgentCapabilities,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
)
from a2a.server.request_handlers import RequestHandler
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskStore, InMemoryTaskStore
from a2a.utils.constants import TransportProtocol

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    CallerIdConstants,
    Channels,
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
from microsoft_agents.hosting.core.channel_adapter_protocol import (
    ChannelAdapterProtocol,
)
from microsoft_agents.hosting.core.http._http_request_protocol import (
    HttpRequestProtocol,
)

from .request_handling import (
    A2AHttpAdapter,
    A2ARequestHandler,
    AgentRequestContext,
)

from .activity import utils, A2AActivity

from .server._constants import _CLAIMS_IDENTITY_KEY

logger = logging.getLogger(__name__)


class A2AAdapter(A2AHttpAdapter, ChannelAdapter, ChannelAdapterProtocol):
    """Adapter for handling Agent-to-Agent (A2A) communication within the Microsoft Agents framework."""

    def __init__(
        self,
        agent: Agent,
        *,
        agent_card_name: str = "A2AAdapter",
        agent_card_description: str = "Agents SDK A2A",
        agent_card_version: str = "0.0.0",
        agent_interfaces: list[AgentInterface] | None = None,
        skills: list[AgentSkill] | None = None,
        task_store: TaskStore | None = None
    ):
        """Initializes the A2AAdapter with the given agent and optional task store.

        :param agent: The agent instance to be used by the adapter.
        :param agent_card_name: The name of the agent card.
        :param agent_card_description: The description of the agent card.
        :param agent_card_version: The version of the agent card.
        :param agent_interfaces: The list of agent interfaces associated with the adapter.
        :param skills: The list of skills associated with the adapter.
        :param task_store: Optional task store for managing tasks. If not provided, an in-memory task store will be used.
        """

        self._agent = agent
        self._agent_card_name = agent_card_name
        self._agent_card_description = agent_card_description
        self._agent_card_version = agent_card_version
        self._task_store = task_store or InMemoryTaskStore()

        self._skills: list[AgentSkill] = skills or []
        self._agent_interfaces: list[AgentInterface] = agent_interfaces or [
            AgentInterface(
                url="/a2a",
                protocol_binding=TransportProtocol.JSONRPC,
            )
        ]
        
        self._a2a_request_handler = A2ARequestHandler(
            self,
            task_store=self._task_store,
            agent_card=self._get_basic_agent_card(),
        )
        self._context_map: dict[str, AgentRequestContext] = {}

    @property
    def skills(self) -> list[AgentSkill]:
        """Get the list of skills associated with the adapter."""
        return self._skills

    @property
    def agent_interfaces(self) -> list[AgentInterface]:
        """Get the list of agent interfaces associated with the adapter."""
        return self._agent_interfaces

    @property
    def a2a_request_handler(self) -> RequestHandler:
        """Get the A2A request handler."""
        return self._a2a_request_handler

    async def execute_agent_turn(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute an agent turn given the request context and event queue.

        :param context: The request context for the agent turn.
        :param event_queue: The event queue for the agent turn.
        """

        if not context.message:
            raise ValueError("Context message is required.")

        identity = context.call_context.state.get(
            _CLAIMS_IDENTITY_KEY, ClaimsIdentity()
        )
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

        try:
            await self._process_activity_with_a2a(
                identity,
                activity,
                context,
                event_queue,
            )
        finally:
            del self._context_map[request_id]

    def _create_turn_context(
        self,
        claims_identity: ClaimsIdentity,
        oauth_scope: str | None = None,
        activity: Activity | None = None,
    ) -> TurnContext:
        """Create a turn context for the given claims identity, OAuth scope, and activity.

        :param claims_identity: The claims identity for the turn context.
        :param oauth_scope: The OAuth scope for the turn context.
        :param activity: The activity for the turn context.
        :return: The created turn context.
        """
        context = TurnContext(self, activity, claims_identity)
        context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY] = oauth_scope
        context.turn_state[ChannelServiceAdapter.AGENT_IDENTITY_KEY] = (
            claims_identity  # for back-compat
        )
        return context

    async def _process_activity_with_a2a(
        self,
        identity: ClaimsIdentity,
        activity: Activity,
        request_context: RequestContext,
        event_queue: EventQueue,
    ) -> InvokeResponse | None:
        """Process an activity with the A2A adapter.

        :param identity: The claims identity of the agent.
        :param activity: The activity to process.
        :param request_context: The request context for the activity.
        :param event_queue: The event queue for the activity.
        :return: An InvokeResponse if applicable, otherwise None.
        """

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
        context.services.set(TaskStore, self._task_store)

        await self.run_pipeline(context, self._agent.on_turn)

    async def send_activities(
        self, context: TurnContext, activities: list[Activity]
    ) -> list[ResourceResponse]:
        """Send activities through the A2A adapter.

        :param context: The turn context for the activities.
        :param activities: The list of activities to send.
        :return: A list of resource responses.
        """

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

    async def _on_streaming_response(
        self, context: TurnContext, activity: Activity, entity: StreamInfo
    ):
        """Handle a streaming response activity.

        :param context: The turn context for the activity.
        :param activity: The activity containing the streaming response.
        :param entity: The streaming entity associated with the activity.
        """
        message = utils.get_incoming_message(context)
        is_informative = entity.stream_type == "informative"

        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        if is_informative:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=message.task_id,
                    context_id=message.context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_WORKING,
                        timestamp=datetime.now(timezone.utc),
                        message=utils.create_message(
                            message.context_id, message.task_id, activity
                        ),
                    ),
                )
            )
        else:
            artifact = utils.activity_to_artifact(activity, entity.stream_id)
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=message.task_id,
                    context_id=message.context_id,
                    artifact=artifact,
                    append=False,
                    last_chunk=True,
                )
            )

    async def _on_message_response(self, context: TurnContext, activity: Activity):
        """Handle a message response activity.

        :param context: The turn context for the activity.
        :param activity: The activity containing the message response.
        """
        message = utils.get_incoming_message(context)
        state = utils.get_task_state(activity)
        response = utils.create_message(message.context_id, message.task_id, activity)

        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=message.task_id,
                context_id=message.context_id,
                status=TaskStatus(
                    state=state, timestamp=datetime.now(timezone.utc), message=response
                ),
            )
        )

    async def _on_end_of_conversation_response(
        self, context: TurnContext, activity: Activity
    ):
        """Handle an end-of-conversation response activity.

        :param context: The turn context for the activity.
        :param activity: The activity containing the end-of-conversation response.
        """
        message = utils.get_incoming_message(context)
        event_queue = context.services.get(EventQueue, raise_if_missing=True)

        if isinstance(activity.value, dict):
            artifact = utils.create_artifact_from_data(
                activity.value,
                name="Result",
                description="Task completion result",
                media_type="application/json",
            )
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=message.task_id,
                    context_id=message.context_id,
                    artifact=artifact,
                    append=False,
                    last_chunk=True,
                )
            )

        task_state: TaskState
        if activity.code == EndOfConversationCodes.error:
            task_state = TaskState.TASK_STATE_FAILED
        elif activity.code == EndOfConversationCodes.user_cancelled:
            task_state = TaskState.TASK_STATE_CANCELED
        else:
            task_state = TaskState.TASK_STATE_COMPLETED

        status_message: Activity | None = None
        if utils.has_message_content(activity):
            status_message = activity.model_copy()
            status_message.value = None

        response = utils.create_message(
            message.context_id,
            message.task_id,
            status_message,
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=message.task_id,
                context_id=message.context_id,
                status=TaskStatus(
                    state=task_state,
                    timestamp=datetime.now(timezone.utc),
                    message=response,
                ),
            )
        )

    def _get_basic_agent_card(self) -> AgentCard:
        """Get the basic agent card with default settings."""
        return AgentCard(
            name=self._agent_card_name,
            description=self._agent_card_description,
            version=self._agent_card_version,
            security_schemes={
                "jwt": SecurityScheme(
                    http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="bearer")
                )
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

    async def get_agent_card(self, request: HttpRequestProtocol, path_prefix: str) -> AgentCard:
        """Get the agent card for the current agent, potentially customized based on the request.

        Set as asynchronous because in some implementations, fetching or customizing the agent card might involve I/O operations, such as querying a database or an external service.
        
        :param request: The HTTP request object conforming to HttpRequestProtocol.
        :param path_prefix: The prefix to be used for constructing the agent interface URL.
        :return: An AgentCard instance representing the agent's capabilities.
        """
        agent_card = self._get_basic_agent_card()

        url_parts = urlsplit(request.url)
        
        if not self._agent_interfaces:
            agent_card.supported_interfaces.append(
                AgentInterface(
                    protocol_binding=TransportProtocol.JSONRPC,
                    url=f"{url_parts.scheme}://{url_parts.hostname}{path_prefix}/",
                    protocol_version="1.0",
                )
            )
        else:
            for agent_interface in self._agent_interfaces:
                if agent_interface.protocol_binding in (
                    TransportProtocol.JSONRPC,
                    TransportProtocol.HTTP_JSON,
                ):
                    agent_card.supported_interfaces.append(AgentInterface(
                        protocol_binding=agent_interface.protocol_binding,
                        url=agent_interface.url,
                        protocol_version="1.0",
                    ))
                else:
                    logger.info("Unsupported protocol: %s", agent_interface.protocol_binding)

        if self._skills:
            for skill_info in self._skills:
                agent_card.skills.append(
                    AgentSkill(
                        id=skill_info.id,
                        name=skill_info.name,
                        description=skill_info.description,
                        tags=skill_info.tags,
                        examples=skill_info.examples,
                        input_modes=skill_info.input_modes,
                        output_modes=skill_info.output_modes,
                    )
                )
        return agent_card

    
    async def update_activity(self, context: TurnContext, activity: Activity) -> None:
        raise NotImplementedError("A2AAdapter.update_activity is not implemented.")

    async def delete_activity(self, context: TurnContext, activity_id: str) -> None:
        raise NotImplementedError("A2AAdapter.delete_activity is not implemented.")
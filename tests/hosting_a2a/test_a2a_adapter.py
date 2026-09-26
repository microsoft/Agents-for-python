# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue, EventQueueLegacy
from a2a.server.tasks import InMemoryTaskStore, TaskStore
from a2a.types import (
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageRequest,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a.utils.constants import TransportProtocol
from google.protobuf.json_format import MessageToDict

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    CallerIdConstants,
    Channels,
    EndOfConversationCodes,
    InputHints,
    StreamInfo,
)
from microsoft_agents.hosting.core import (
    AuthenticationConstants,
    ChannelServiceAdapter,
    ClaimsIdentity,
    TurnContext,
)
from microsoft_agents.hosting.a2a import A2AAdapter
from microsoft_agents.hosting.a2a.activity import A2AActivity
from microsoft_agents.hosting.a2a.server._constants import _CLAIMS_IDENTITY_KEY


def _agent():
    return SimpleNamespace(on_turn=AsyncMock())


def _message() -> Message:
    return Message(
        message_id="message-1",
        task_id="task-1",
        context_id="context-1",
        role=Role.ROLE_USER,
        parts=[Part(text="hello")],
    )


def _request_context(identity=None, *, include_message=True):
    call_context = ServerCallContext(
        state={} if identity is None else {_CLAIMS_IDENTITY_KEY: identity}
    )
    request = SendMessageRequest(message=_message()) if include_message else None
    return RequestContext(
        call_context,
        request=request,
        task_id="task-1",
        context_id="context-1",
    )


def _turn_context(adapter, event_queue):
    context = TurnContext(
        adapter,
        A2AActivity(
            type=ActivityTypes.message,
            channel_data=_message(),
        ),
        ClaimsIdentity(),
    )
    context.services.set(EventQueue, event_queue)
    return context


def test_constructor_uses_defaults_and_creates_request_handler():
    adapter = A2AAdapter(_agent())

    assert adapter.agent_interfaces == []
    assert adapter.skills == []
    assert adapter.a2a_request_handler is not None


def test_constructor_preserves_custom_interfaces_and_skills():
    interface = AgentInterface(
        url="https://example.com/a2a",
        protocol_binding=TransportProtocol.HTTP_JSON,
    )
    skill = AgentSkill(
        id="weather",
        name="Weather",
        description="Gets weather",
        tags=["weather"],
    )
    task_store = InMemoryTaskStore()

    adapter = A2AAdapter(
        _agent(),
        agent_interfaces=[interface],
        skills=[skill],
        task_store=task_store,
    )

    assert adapter.agent_interfaces == [interface]
    assert adapter.skills == [skill]


@pytest.mark.asyncio
async def test_execute_agent_turn_requires_message():
    adapter = A2AAdapter(_agent())

    with pytest.raises(ValueError, match="Context message is required"):
        await adapter.execute_agent_turn(
            _request_context(include_message=False),
            MagicMock(spec=EventQueue),
        )


@pytest.mark.asyncio
async def test_execute_agent_turn_rejects_invalid_identity():
    adapter = A2AAdapter(_agent())
    context = _request_context(identity="invalid")

    with pytest.raises(RuntimeError, match="Invalid identity"):
        await adapter.execute_agent_turn(context, MagicMock(spec=EventQueue))


@pytest.mark.asyncio
async def test_execute_agent_turn_converts_message_and_exposes_a2a_services():
    identity = ClaimsIdentity({"sub": "agent-1"})
    context = _request_context(identity)
    event_queue = EventQueueLegacy()
    task_store = InMemoryTaskStore()
    observed = {}

    async def on_turn(turn_context):
        observed["context"] = turn_context

    adapter = A2AAdapter(
        SimpleNamespace(on_turn=on_turn),
        task_store=task_store,
    )

    await adapter.execute_agent_turn(context, event_queue)

    turn_context = observed["context"]
    assert turn_context.identity is identity
    assert isinstance(turn_context.activity, A2AActivity)
    assert turn_context.activity.text == "hello"
    assert turn_context.activity.request_id
    assert turn_context.services.get(RequestContext) is context
    assert turn_context.services.get(EventQueue) is event_queue
    assert turn_context.services.get(TaskStore) is task_store
    assert (
        turn_context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY]
        == AuthenticationConstants.AGENTS_SDK_SCOPE
    )


@pytest.mark.asyncio
async def test_cancel_agent_turn_delivers_user_cancelled_activity():
    identity = ClaimsIdentity({"sub": "agent-1"})
    context = _request_context(identity, include_message=False)
    event_queue = EventQueueLegacy()
    observed = {}

    async def on_turn(turn_context):
        observed["context"] = turn_context

    adapter = A2AAdapter(SimpleNamespace(on_turn=on_turn))

    await adapter.cancel_agent_turn(context, event_queue)

    turn_context = observed["context"]
    activity = turn_context.activity
    assert turn_context.identity is identity
    assert activity.type == ActivityTypes.end_of_conversation
    assert activity.code == EndOfConversationCodes.user_cancelled
    assert activity.channel_id == Channels.a2a
    assert activity.recipient.id == "assistant"
    assert activity.from_property.id == "unknown"
    assert turn_context.services.get(RequestContext) is context
    assert turn_context.services.get(EventQueue) is event_queue


@pytest.mark.asyncio
async def test_cancel_agent_turn_uses_anonymous_identity_by_default():
    context = _request_context(include_message=False)
    observed = {}

    async def on_turn(turn_context):
        observed["identity"] = turn_context.identity

    adapter = A2AAdapter(SimpleNamespace(on_turn=on_turn))

    await adapter.cancel_agent_turn(context, EventQueueLegacy())

    identity = observed["identity"]
    assert isinstance(identity, ClaimsIdentity)
    assert identity.allow_anonymous is True


@pytest.mark.asyncio
async def test_cancel_agent_turn_rejects_invalid_identity():
    context = _request_context(identity="invalid", include_message=False)
    adapter = A2AAdapter(_agent())

    with pytest.raises(RuntimeError, match="Invalid identity"):
        await adapter.cancel_agent_turn(context, EventQueueLegacy())


@pytest.mark.asyncio
async def test_execute_agent_turn_sets_agent_caller_and_audience():
    identity = ClaimsIdentity(
        {
            AuthenticationConstants.VERSION_CLAIM: "2.0",
            AuthenticationConstants.AUDIENCE_CLAIM: "target-agent",
            AuthenticationConstants.AUTHORIZED_PARTY: "calling-agent",
        }
    )
    observed = {}

    async def on_turn(turn_context):
        observed["context"] = turn_context

    adapter = A2AAdapter(SimpleNamespace(on_turn=on_turn))

    await adapter.execute_agent_turn(
        _request_context(identity),
        EventQueueLegacy(),
    )

    context = observed["context"]
    assert (
        context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY]
        == "app://calling-agent"
    )
    assert context.activity.caller_id == (
        f"{CallerIdConstants.agent_to_agent_prefix}calling-agent"
    )


@pytest.mark.asyncio
async def test_send_activities_emits_protocol_events_for_supported_activities():
    adapter = A2AAdapter(_agent())
    event_queue = EventQueueLegacy()
    context = _turn_context(adapter, event_queue)
    stream_info = StreamInfo(
        stream_id="stream-1",
        stream_type="content",
        stream_sequence=1,
    )
    streaming = A2AActivity(
        type=ActivityTypes.message,
        text="chunk",
        entities=[stream_info],
    )
    message = A2AActivity(
        type=ActivityTypes.message,
        text="working",
        input_hint=InputHints.expecting_input,
    )
    completed = A2AActivity(
        type=ActivityTypes.end_of_conversation,
        code=EndOfConversationCodes.completed_successfully,
    )
    ignored = Activity(
        type=ActivityTypes.message,
        channel_id=Channels.webchat,
    )

    result = await adapter.send_activities(
        context,
        [streaming, message, completed, ignored],
    )

    assert result == []
    artifact_event = await event_queue.dequeue_event()
    message_event = await event_queue.dequeue_event()
    completed_event = await event_queue.dequeue_event()

    assert isinstance(artifact_event, TaskArtifactUpdateEvent)
    assert artifact_event.task_id == "task-1"
    assert artifact_event.context_id == "context-1"
    assert artifact_event.artifact.artifact_id == "stream-1"
    assert artifact_event.artifact.parts[0].text == "chunk"

    assert isinstance(message_event, TaskStatusUpdateEvent)
    assert message_event.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    assert message_event.status.message.parts[0].text == "working"

    assert isinstance(completed_event, TaskStatusUpdateEvent)
    assert completed_event.status.state == TaskState.TASK_STATE_COMPLETED
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(event_queue.dequeue_event(), timeout=0.05)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "expected_state"),
    [
        (EndOfConversationCodes.completed_successfully, TaskState.TASK_STATE_COMPLETED),
        (EndOfConversationCodes.error, TaskState.TASK_STATE_FAILED),
        (EndOfConversationCodes.user_cancelled, TaskState.TASK_STATE_CANCELED),
    ],
)
async def test_end_of_conversation_maps_terminal_state(code, expected_state):
    event_queue = EventQueueLegacy()
    adapter = A2AAdapter(_agent())
    context = _turn_context(adapter, event_queue)
    activity = A2AActivity(
        type=ActivityTypes.end_of_conversation,
        code=code,
    )

    await adapter.send_activities(context, [activity])

    event = await event_queue.dequeue_event()
    assert isinstance(event, TaskStatusUpdateEvent)
    assert event.status.state == expected_state


@pytest.mark.asyncio
async def test_end_of_conversation_emits_result_artifact_before_status_message():
    event_queue = EventQueueLegacy()
    adapter = A2AAdapter(_agent())
    context = _turn_context(adapter, event_queue)
    activity = A2AActivity(
        type=ActivityTypes.end_of_conversation,
        code=EndOfConversationCodes.completed_successfully,
        text="Completed with structured data",
        value={"answer": 42},
    )

    await adapter.send_activities(context, [activity])

    artifact_event = await event_queue.dequeue_event()
    status_event = await event_queue.dequeue_event()

    assert isinstance(artifact_event, TaskArtifactUpdateEvent)
    assert artifact_event.last_chunk is True
    assert artifact_event.artifact.name == "Result"
    assert MessageToDict(artifact_event.artifact.parts[0].data) == {"answer": 42.0}

    assert isinstance(status_event, TaskStatusUpdateEvent)
    assert status_event.status.state == TaskState.TASK_STATE_COMPLETED
    assert status_event.status.message.parts[0].text == (
        "Completed with structured data"
    )
    assert all(not part.HasField("data") for part in status_event.status.message.parts)


@pytest.mark.asyncio
async def test_get_agent_card_projects_interfaces_and_skills():
    interface = AgentInterface(
        url="https://example.com/a2a",
        protocol_binding=TransportProtocol.HTTP_JSON,
    )
    skill = AgentSkill(
        id="weather",
        name="Weather",
        description="Gets weather",
        tags=["weather"],
        examples=["Weather in Seattle"],
        input_modes=["text/plain"],
        output_modes=["application/json"],
    )
    adapter = A2AAdapter(
        _agent(),
        agent_card_name="Test agent",
        agent_card_description="Description",
        agent_card_version="1.2.3",
        agent_interfaces=[interface],
        skills=[skill],
    )

    card = await adapter.get_agent_card(
        SimpleNamespace(url="https://host.example/a2a/card"),
        "/a2a",
    )

    assert card.name == "Test agent"
    assert card.description == "Description"
    assert card.version == "1.2.3"
    assert card.supported_interfaces[0].url == "https://example.com/a2a"
    assert card.supported_interfaces[0].protocol_binding == TransportProtocol.HTTP_JSON
    assert card.supported_interfaces[0].protocol_version == "1.0"
    assert card.skills[0].id == "weather"
    assert card.skills[0].examples == ["Weather in Seattle"]


@pytest.mark.asyncio
async def test_get_agent_card_resolves_relative_interface_against_request_origin():
    adapter = A2AAdapter(
        _agent(),
        agent_interfaces=[
            AgentInterface(
                url="/a2a",
                protocol_binding=TransportProtocol.JSONRPC,
            )
        ],
    )

    card = await adapter.get_agent_card(
        SimpleNamespace(url="http://127.0.0.1:41241/a2a/.well-known/agent-card.json"),
        "/a2a",
    )

    assert card.supported_interfaces[0].url == "http://127.0.0.1:41241/a2a"


@pytest.mark.asyncio
async def test_update_and_delete_activity_are_not_supported():
    adapter = A2AAdapter(_agent())

    with pytest.raises(NotImplementedError):
        await adapter.update_activity(
            MagicMock(spec=TurnContext),
            Activity(type=ActivityTypes.message),
        )

    with pytest.raises(NotImplementedError):
        await adapter.delete_activity(MagicMock(spec=TurnContext), "activity-1")

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue
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
    request = (
        SendMessageRequest(message=_message())
        if include_message
        else None
    )
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

    assert isinstance(adapter._task_store, InMemoryTaskStore)
    assert adapter.agent_interfaces == []
    assert adapter.skills == []
    assert adapter.a2a_request_handler is not None


def test_constructor_preserves_custom_interfaces_skills_and_task_store():
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
    assert adapter._task_store is task_store


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
async def test_execute_agent_turn_converts_message_and_processes_activity():
    identity = ClaimsIdentity({"sub": "agent-1"})
    context = _request_context(identity)
    event_queue = MagicMock(spec=EventQueue)
    adapter = A2AAdapter(_agent())
    adapter._process_activity_with_a2a = AsyncMock()

    await adapter.execute_agent_turn(context, event_queue)

    adapter._process_activity_with_a2a.assert_awaited_once()
    actual_identity, activity, actual_context, actual_queue = (
        adapter._process_activity_with_a2a.call_args.args
    )
    assert actual_identity is identity
    assert isinstance(activity, A2AActivity)
    assert activity.text == "hello"
    assert activity.request_id
    assert actual_context is context
    assert actual_queue is event_queue


@pytest.mark.asyncio
async def test_cancel_agent_turn_processes_user_cancelled_activity():
    identity = ClaimsIdentity({"sub": "agent-1"})
    context = _request_context(identity, include_message=False)
    event_queue = MagicMock(spec=EventQueue)
    adapter = A2AAdapter(_agent())
    adapter._process_activity_with_a2a = AsyncMock()

    await adapter.cancel_agent_turn(context, event_queue)

    adapter._process_activity_with_a2a.assert_awaited_once()
    actual_identity, activity, actual_context, actual_queue = (
        adapter._process_activity_with_a2a.call_args.args
    )
    assert actual_identity is identity
    assert activity.type == ActivityTypes.end_of_conversation
    assert activity.code == EndOfConversationCodes.user_cancelled
    assert activity.channel_id == Channels.a2a
    assert activity.recipient.id == "assistant"
    assert activity.from_property.id == "unknown"
    assert actual_context is context
    assert actual_queue is event_queue


@pytest.mark.asyncio
async def test_cancel_agent_turn_uses_anonymous_identity_by_default():
    context = _request_context(include_message=False)
    adapter = A2AAdapter(_agent())
    adapter._process_activity_with_a2a = AsyncMock()

    await adapter.cancel_agent_turn(context, MagicMock(spec=EventQueue))

    identity = adapter._process_activity_with_a2a.call_args.args[0]
    assert isinstance(identity, ClaimsIdentity)
    assert identity.allow_anonymous is True


@pytest.mark.asyncio
async def test_cancel_agent_turn_rejects_invalid_identity():
    context = _request_context(identity="invalid", include_message=False)
    adapter = A2AAdapter(_agent())
    adapter._process_activity_with_a2a = AsyncMock()

    with pytest.raises(RuntimeError, match="Invalid identity"):
        await adapter.cancel_agent_turn(context, MagicMock(spec=EventQueue))

    adapter._process_activity_with_a2a.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_activity_registers_services_and_runs_agent_pipeline():
    agent = _agent()
    adapter = A2AAdapter(agent)
    adapter.run_pipeline = AsyncMock()
    identity = ClaimsIdentity()
    request_context = MagicMock(spec=RequestContext)
    event_queue = MagicMock(spec=EventQueue)
    activity = A2AActivity(type=ActivityTypes.message)

    await adapter._process_activity_with_a2a(
        identity,
        activity,
        request_context,
        event_queue,
    )

    adapter.run_pipeline.assert_awaited_once()
    context, handler = adapter.run_pipeline.call_args.args
    assert handler is agent.on_turn
    assert context.identity is identity
    assert (
        context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY]
        == AuthenticationConstants.AGENTS_SDK_SCOPE
    )
    assert context.services.get(RequestContext) is request_context
    assert context.services.get(EventQueue) is event_queue
    assert context.services.get(TaskStore) is adapter._task_store


@pytest.mark.asyncio
async def test_process_activity_sets_agent_caller_and_audience():
    identity = ClaimsIdentity(
        {
            AuthenticationConstants.VERSION_CLAIM: "2.0",
            AuthenticationConstants.AUDIENCE_CLAIM: "target-agent",
            AuthenticationConstants.AUTHORIZED_PARTY: "calling-agent",
        }
    )
    adapter = A2AAdapter(_agent())
    adapter.run_pipeline = AsyncMock()
    activity = A2AActivity(type=ActivityTypes.message)

    await adapter._process_activity_with_a2a(
        identity,
        activity,
        MagicMock(spec=RequestContext),
        MagicMock(spec=EventQueue),
    )

    context = adapter.run_pipeline.call_args.args[0]
    assert (
        context.turn_state[ChannelServiceAdapter.OAUTH_SCOPE_KEY]
        == "app://calling-agent"
    )
    assert activity.caller_id == (
        f"{CallerIdConstants.agent_to_agent_prefix}calling-agent"
    )


@pytest.mark.asyncio
async def test_process_activity_rejects_non_a2a_channel():
    adapter = A2AAdapter(_agent())

    with pytest.raises(ValueError, match="channel_id must be 'a2a'"):
        await adapter._process_activity_with_a2a(
            ClaimsIdentity(),
            Activity(type=ActivityTypes.message, channel_id=Channels.webchat),
            MagicMock(spec=RequestContext),
            MagicMock(spec=EventQueue),
        )


@pytest.mark.asyncio
async def test_send_activities_dispatches_supported_activity_types():
    adapter = A2AAdapter(_agent())
    adapter._on_streaming_response = AsyncMock()
    adapter._on_message_response = AsyncMock()
    adapter._on_end_of_conversation_response = AsyncMock()
    context = MagicMock(spec=TurnContext)
    stream_info = StreamInfo(
        stream_id="stream-1",
        stream_type="informative",
        stream_sequence=1,
    )
    streaming = A2AActivity(
        type=ActivityTypes.message,
        entities=[stream_info],
    )
    message = A2AActivity(type=ActivityTypes.message, text="hello")
    completed = A2AActivity(type=ActivityTypes.end_of_conversation)
    ignored = Activity(
        type=ActivityTypes.message,
        channel_id=Channels.webchat,
    )

    result = await adapter.send_activities(
        context,
        [streaming, message, completed, ignored],
    )

    assert result == []
    adapter._on_streaming_response.assert_awaited_once_with(
        context,
        streaming,
        stream_info,
    )
    adapter._on_message_response.assert_awaited_once_with(context, message)
    adapter._on_end_of_conversation_response.assert_awaited_once_with(
        context,
        completed,
    )


@pytest.mark.asyncio
async def test_message_response_enqueues_status_update():
    event_queue = MagicMock(spec=EventQueue)
    event_queue.enqueue_event = AsyncMock()
    adapter = A2AAdapter(_agent())
    context = _turn_context(adapter, event_queue)
    activity = A2AActivity(
        type=ActivityTypes.message,
        text="working",
        input_hint=InputHints.expecting_input,
    )

    await adapter._on_message_response(context, activity)

    event = event_queue.enqueue_event.call_args.args[0]
    assert isinstance(event, TaskStatusUpdateEvent)
    assert event.task_id == "task-1"
    assert event.context_id == "context-1"
    assert event.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    assert event.status.message.parts[0].text == "working"


@pytest.mark.asyncio
async def test_streaming_response_enqueues_artifact_update():
    event_queue = MagicMock(spec=EventQueue)
    event_queue.enqueue_event = AsyncMock()
    adapter = A2AAdapter(_agent())
    context = _turn_context(adapter, event_queue)
    activity = A2AActivity(type=ActivityTypes.message, text="chunk")
    stream_info = StreamInfo(
        stream_id="artifact-1",
        stream_type="content",
        stream_sequence=1,
    )

    await adapter._on_streaming_response(context, activity, stream_info)

    event = event_queue.enqueue_event.call_args.args[0]
    assert isinstance(event, TaskArtifactUpdateEvent)
    assert event.task_id == "task-1"
    assert event.context_id == "context-1"
    assert event.artifact.artifact_id == "artifact-1"
    assert event.artifact.parts[0].text == "chunk"
    assert event.last_chunk is False


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
    event_queue = MagicMock(spec=EventQueue)
    event_queue.enqueue_event = AsyncMock()
    adapter = A2AAdapter(_agent())
    context = _turn_context(adapter, event_queue)
    activity = A2AActivity(
        type=ActivityTypes.end_of_conversation,
        code=code,
    )

    await adapter._on_end_of_conversation_response(context, activity)

    event = event_queue.enqueue_event.call_args.args[0]
    assert isinstance(event, TaskStatusUpdateEvent)
    assert event.status.state == expected_state


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
    assert (
        card.supported_interfaces[0].protocol_binding
        == TransportProtocol.HTTP_JSON
    )
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

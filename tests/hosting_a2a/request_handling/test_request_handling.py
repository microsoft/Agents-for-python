# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueueLegacy
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    CancelTaskRequest,
    GetExtendedAgentCardRequest,
    GetTaskRequest,
    ListTasksRequest,
    Message,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils.errors import (
    ExtendedAgentCardNotConfiguredError,
    UnsupportedOperationError,
)

from microsoft_agents.hosting.a2a.request_handling import (
    A2AAgentExecutor,
    A2ARequestHandler,
)

pytestmark = pytest.mark.filterwarnings(
    "ignore:label\\(\\) is deprecated\\. Use is_required\\(\\) or is_repeated\\(\\) instead\\.:DeprecationWarning"
)


def _agent_card(name: str = "Test agent") -> AgentCard:
    return AgentCard(
        name=name,
        description="Test agent description",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(
                url="https://example.com/a2a",
                protocol_binding="JSONRPC",
            )
        ],
        capabilities=AgentCapabilities(),
    )


def _message(
    text: str,
    *,
    message_id: str,
    role: Role = Role.ROLE_USER,
    task_id: str = "",
    context_id: str = "",
) -> Message:
    return Message(
        message_id=message_id,
        role=role,
        task_id=task_id,
        context_id=context_id,
        parts=[Part(text=text)],
    )


def _send_request(
    text: str,
    *,
    message_id: str,
    task_id: str = "",
    context_id: str = "",
) -> SendMessageRequest:
    return SendMessageRequest(
        message=_message(
            text,
            message_id=message_id,
            task_id=task_id,
            context_id=context_id,
        )
    )


def _history_text(task: Task) -> list[str]:
    return [message.parts[0].text for message in task.history]


def _status_text(task: Task) -> str | None:
    if not task.status.HasField("message"):
        return None
    return task.status.message.parts[0].text


async def _wait_for_task_state(task_store, task_id, call_context, expected_state):
    async def wait():
        while True:
            task = await task_store.get(task_id, call_context)
            if task is not None and task.status.state == expected_state:
                return task
            await asyncio.sleep(0)

    return await asyncio.wait_for(wait(), timeout=1)


class _CompletingAdapter:
    def __init__(self) -> None:
        self.contexts: list[RequestContext] = []

    async def execute_agent_turn(self, context, event_queue) -> None:
        self.contexts.append(context)
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )
        await updater.complete(
            _message(
                "completed",
                message_id="response-1",
                role=Role.ROLE_AGENT,
                task_id=context.task_id,
                context_id=context.context_id,
            )
        )

    async def cancel_agent_turn(self, context, event_queue) -> None:
        raise AssertionError("Completed tasks should not be canceled")


class _InputThenCompleteAdapter:
    def __init__(self) -> None:
        self.contexts: list[RequestContext] = []
        self.current_task_states: list[int | None] = []

    async def execute_agent_turn(self, context, event_queue) -> None:
        self.contexts.append(context)
        self.current_task_states.append(
            context.current_task.status.state if context.current_task else None
        )
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )

        if len(self.contexts) == 1:
            await updater.update_status(
                TaskState.TASK_STATE_INPUT_REQUIRED,
                _message(
                    "More information required",
                    message_id="prompt-1",
                    role=Role.ROLE_AGENT,
                    task_id=context.task_id,
                    context_id=context.context_id,
                ),
            )
            return

        await updater.complete(
            _message(
                "Request completed",
                message_id="response-2",
                role=Role.ROLE_AGENT,
                task_id=context.task_id,
                context_id=context.context_id,
            )
        )

    async def cancel_agent_turn(self, context, event_queue) -> None:
        raise AssertionError("This task should not be canceled")


class _CancelableAdapter:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.cancel_context: RequestContext | None = None

    async def execute_agent_turn(self, context, event_queue) -> None:
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )
        await updater.start_work()
        self.started.set()
        await asyncio.Event().wait()

    async def cancel_agent_turn(self, context, event_queue) -> None:
        self.cancel_context = context


class _FailingAdapter:
    async def execute_agent_turn(self, context, event_queue) -> None:
        raise RuntimeError("agent failed")

    async def cancel_agent_turn(self, context, event_queue) -> None:
        raise AssertionError("Failed tasks should not be canceled")


@pytest.mark.asyncio
async def test_executor_establishes_task_mode_before_adapter_events():
    adapter = _CompletingAdapter()
    executor = A2AAgentExecutor(adapter)
    request = _send_request("hello", message_id="message-1")
    context = RequestContext(
        ServerCallContext(),
        request=request,
        task_id="task-1",
        context_id="context-1",
    )
    event_queue = EventQueueLegacy()

    await executor.execute(context, event_queue)

    initial_task = await event_queue.dequeue_event()
    completion = await event_queue.dequeue_event()

    assert isinstance(initial_task, Task)
    assert initial_task.id == "task-1"
    assert initial_task.context_id == "context-1"
    assert initial_task.status.state == TaskState.TASK_STATE_SUBMITTED
    assert initial_task.status.HasField("timestamp")
    assert list(initial_task.history) == [request.message]

    assert isinstance(completion, TaskStatusUpdateEvent)
    assert completion.task_id == initial_task.id
    assert completion.context_id == initial_task.context_id
    assert completion.status.state == TaskState.TASK_STATE_COMPLETED


@pytest.mark.asyncio
async def test_executor_continuation_updates_existing_task_without_replacing_it():
    adapter = _CompletingAdapter()
    executor = A2AAgentExecutor(adapter)
    existing_task = Task(
        id="task-1",
        context_id="context-1",
        status=TaskStatus(state=TaskState.TASK_STATE_INPUT_REQUIRED),
    )
    context = RequestContext(
        ServerCallContext(),
        request=_send_request(
            "additional input",
            message_id="message-2",
            task_id=existing_task.id,
            context_id=existing_task.context_id,
        ),
        task_id=existing_task.id,
        context_id=existing_task.context_id,
        task=existing_task,
    )
    event_queue = EventQueueLegacy()

    await executor.execute(context, event_queue)

    event = await event_queue.dequeue_event()
    assert isinstance(event, TaskStatusUpdateEvent)
    assert event.task_id == existing_task.id
    assert event.status.state == TaskState.TASK_STATE_COMPLETED
    assert adapter.contexts[0].current_task is existing_task


@pytest.mark.asyncio
async def test_request_handler_completes_persists_and_queries_task():
    adapter = _CompletingAdapter()
    task_store = InMemoryTaskStore()
    handler = A2ARequestHandler(adapter, task_store, _agent_card())
    call_context = ServerCallContext()
    request = _send_request("hello", message_id="message-1")

    try:
        result = await handler.on_message_send(request, call_context)

        assert isinstance(result, Task)
        assert result.status.state == TaskState.TASK_STATE_COMPLETED
        assert request.message.task_id == result.id
        assert request.message.context_id == result.context_id
        assert _history_text(result) == ["hello"]
        assert _status_text(result) == "completed"
        assert adapter.contexts[0].current_task is None

        stored = await task_store.get(result.id, call_context)
        assert stored == result

        without_history = await handler.on_get_task(
            GetTaskRequest(id=result.id, history_length=0),
            call_context,
        )
        assert _history_text(without_history) == []
        assert _status_text(without_history) == "completed"
        assert _history_text(stored) == ["hello"]

        listed = await handler.on_list_tasks(
            ListTasksRequest(context_id=result.context_id),
            call_context,
        )
        assert [task.id for task in listed.tasks] == [result.id]
        assert _status_text(listed.tasks[0]) == "completed"
    finally:
        await handler.aclose()


@pytest.mark.asyncio
async def test_request_handler_continues_interrupted_task_in_same_a2a_context():
    adapter = _InputThenCompleteAdapter()
    task_store = InMemoryTaskStore()
    handler = A2ARequestHandler(adapter, task_store, _agent_card())
    call_context = ServerCallContext()

    try:
        first_result = await handler.on_message_send(
            _send_request("initial request", message_id="message-1"),
            call_context,
        )

        assert isinstance(first_result, Task)
        assert first_result.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
        assert _history_text(first_result) == ["initial request"]
        assert _status_text(first_result) == "More information required"

        second_result = await handler.on_message_send(
            _send_request(
                "additional input",
                message_id="message-2",
                task_id=first_result.id,
                context_id=first_result.context_id,
            ),
            call_context,
        )

        assert isinstance(second_result, Task)
        assert second_result.id == first_result.id
        assert second_result.context_id == first_result.context_id
        assert second_result.status.state == TaskState.TASK_STATE_COMPLETED
        assert _history_text(second_result) == [
            "initial request",
            "More information required",
            "additional input",
        ]
        assert _status_text(second_result) == "Request completed"
        assert adapter.current_task_states[0] is None
        assert adapter.current_task_states[1] == TaskState.TASK_STATE_INPUT_REQUIRED
        assert adapter.contexts[1].current_task.id == first_result.id
    finally:
        await handler.aclose()


@pytest.mark.asyncio
async def test_request_handler_cancels_and_persists_active_task():
    adapter = _CancelableAdapter()
    task_store = InMemoryTaskStore()
    handler = A2ARequestHandler(adapter, task_store, _agent_card())
    call_context = ServerCallContext()
    request = _send_request("long-running request", message_id="message-1")
    send_call = asyncio.create_task(handler.on_message_send(request, call_context))

    try:
        await asyncio.wait_for(adapter.started.wait(), timeout=1)
        active_task = await _wait_for_task_state(
            task_store,
            request.message.task_id,
            call_context,
            TaskState.TASK_STATE_WORKING,
        )
        canceled = await asyncio.wait_for(
            handler.on_cancel_task(
                CancelTaskRequest(id=request.message.task_id),
                call_context,
            ),
            timeout=1,
        )
        send_result = await asyncio.wait_for(send_call, timeout=1)

        assert canceled.status.state == TaskState.TASK_STATE_CANCELED
        assert send_result == canceled
        assert adapter.cancel_context is not None
        assert adapter.cancel_context.task_id == canceled.id
        assert adapter.cancel_context.context_id == canceled.context_id
        assert active_task.status.state == TaskState.TASK_STATE_WORKING
        assert adapter.cancel_context.current_task.id == active_task.id

        stored = await task_store.get(canceled.id, call_context)
        assert stored == canceled
    finally:
        if not send_call.done():
            send_call.cancel()
        await handler.aclose()


@pytest.mark.asyncio
async def test_request_handler_persists_failed_task_when_adapter_raises():
    task_store = InMemoryTaskStore()
    handler = A2ARequestHandler(_FailingAdapter(), task_store, _agent_card())
    call_context = ServerCallContext()
    request = _send_request("fail", message_id="message-1")

    try:
        with pytest.raises(RuntimeError, match="agent failed"):
            await handler.on_message_send(request, call_context)

        stored = await task_store.get(request.message.task_id, call_context)
        assert stored is not None
        assert stored.status.state == TaskState.TASK_STATE_FAILED
    finally:
        await handler.aclose()


@pytest.mark.asyncio
async def test_request_handler_update_agent_card_changes_extended_card_capability():
    original_card = _agent_card()
    updated_card = _agent_card("Updated agent")
    updated_card.capabilities.extended_agent_card = True
    handler = A2ARequestHandler(
        _CompletingAdapter(),
        InMemoryTaskStore(),
        original_card,
    )

    try:
        with pytest.raises(UnsupportedOperationError):
            await handler.on_get_extended_agent_card(
                GetExtendedAgentCardRequest(),
                ServerCallContext(),
            )

        handler.update_agent_card(updated_card)

        with pytest.raises(ExtendedAgentCardNotConfiguredError):
            await handler.on_get_extended_agent_card(
                GetExtendedAgentCardRequest(),
                ServerCallContext(),
            )
    finally:
        await handler.aclose()

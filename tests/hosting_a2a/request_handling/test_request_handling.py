# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    Message,
    Role,
    Task,
    TaskState,
)

from microsoft_agents.hosting.a2a.request_handling import (
    A2AAgentExecutor,
    A2ARequestHandler,
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


@pytest.mark.asyncio
async def test_executor_delegates_message_to_adapter():
    adapter = SimpleNamespace(execute_agent_turn=AsyncMock())
    executor = A2AAgentExecutor(adapter)
    context = SimpleNamespace(
        message=Message(message_id="message-1", role=Role.ROLE_USER),
        current_task=object(),
    )
    event_queue = AsyncMock(spec=EventQueue)

    await executor.execute(context, event_queue)

    adapter.execute_agent_turn.assert_awaited_once_with(context, event_queue)


@pytest.mark.asyncio
async def test_executor_submits_new_task_before_delegating():
    adapter = SimpleNamespace(execute_agent_turn=AsyncMock())
    executor = A2AAgentExecutor(adapter)
    context = SimpleNamespace(
        message=Message(message_id="message-1", role=Role.ROLE_USER),
        current_task=None,
        task_id="task-1",
        context_id="context-1",
    )
    event_queue = AsyncMock(spec=EventQueue)

    await executor.execute(context, event_queue)

    task = event_queue.enqueue_event.call_args.args[0]
    assert isinstance(task, Task)
    assert task.id == "task-1"
    assert task.context_id == "context-1"
    assert task.status.state == TaskState.TASK_STATE_SUBMITTED
    assert task.status.HasField("timestamp")
    assert list(task.history) == [context.message]
    adapter.execute_agent_turn.assert_awaited_once_with(context, event_queue)


@pytest.mark.asyncio
async def test_executor_drops_context_without_message(caplog):
    adapter = SimpleNamespace(execute_agent_turn=AsyncMock())
    executor = A2AAgentExecutor(adapter)
    context = SimpleNamespace(message=None)
    event_queue = AsyncMock(spec=EventQueue)

    with caplog.at_level("WARNING"):
        await executor.execute(context, event_queue)

    adapter.execute_agent_turn.assert_not_awaited()
    assert "No message found in the request context" in caplog.text


@pytest.mark.asyncio
async def test_executor_cancel_updates_task_without_calling_adapter():
    adapter = SimpleNamespace(execute_agent_turn=AsyncMock())
    executor = A2AAgentExecutor(adapter)
    context = SimpleNamespace(task_id="task-1", context_id="context-1")
    event_queue = AsyncMock(spec=EventQueue)
    updater = AsyncMock()

    with patch(
        "microsoft_agents.hosting.a2a.request_handling."
        "a2a_agent_executor.TaskUpdater",
        return_value=updater,
    ) as task_updater:
        await executor.cancel(context, event_queue)

    task_updater.assert_called_once_with(
        event_queue=event_queue,
        task_id="task-1",
        context_id="context-1",
    )
    updater.cancel.assert_awaited_once()
    adapter.execute_agent_turn.assert_not_awaited()


def test_request_handler_uses_adapter_and_updates_agent_card():
    adapter = SimpleNamespace(execute_agent_turn=AsyncMock())
    original_card = _agent_card()
    updated_card = _agent_card("Updated agent")

    handler = A2ARequestHandler(
        adapter,
        InMemoryTaskStore(),
        original_card,
    )
    handler.update_agent_card(updated_card)

    assert handler._adapter is adapter
    assert handler.agent_executor._adapter is adapter
    assert handler._agent_card is updated_card

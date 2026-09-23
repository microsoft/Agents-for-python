# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import MagicMock

from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue, EventQueueLegacy
from a2a.server.tasks import InMemoryTaskStore, TaskStore

from microsoft_agents.activity import Activity, ResourceResponse
from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    ClaimsIdentity,
    TurnContext,
)
from microsoft_agents.hosting.a2a.activity import A2AActivity
from microsoft_agents.hosting.a2a.a2a_turn_context import A2ATurnContext


class _Adapter(ChannelAdapter):
    async def send_activities(self, context, activities):
        return [ResourceResponse()] * len(activities)

    async def update_activity(self, context, activity):
        return ResourceResponse(id=activity.id)

    async def delete_activity(self, context, reference):
        return None


def _original_context():
    original = TurnContext(
        _Adapter(),
        Activity(type="message", text="hello"),
        ClaimsIdentity(),
    )
    original.services.set(EventQueue, EventQueueLegacy())
    original.services.set(
        RequestContext,
        RequestContext(
            ServerCallContext(),
            task_id="task-1",
            context_id="context-1",
        ),
    )
    original.services.set(TaskStore, InMemoryTaskStore())
    return original


def test_wraps_existing_context_and_exposes_a2a_client():
    original = _original_context()
    context = A2ATurnContext.from_existing(
        original,
        MagicMock(spec=AgentApplication),
    )

    assert isinstance(context.activity, A2AActivity)
    assert context.activity.text == "hello"
    assert context.client.event_queue is original.services.get(EventQueue)
    assert context.client.request_context is original.services.get(RequestContext)
    assert context.client.task_store is original.services.get(TaskStore)


def test_wrapped_context_preserves_original_turn_state():
    original = _original_context()
    marker = object()
    original.turn_state["marker"] = marker

    context = A2ATurnContext.from_existing(
        original,
        MagicMock(spec=AgentApplication),
    )

    assert context.turn_state is original.turn_state
    assert context.turn_state["marker"] is marker


def test_can_be_constructed_directly_from_adapter_activity_and_identity():
    adapter = _Adapter()
    activity = A2AActivity(type="message", text="hello")
    identity = ClaimsIdentity({"sub": "agent-1"})
    request_context = RequestContext(
        ServerCallContext(),
        task_id="task-1",
        context_id="context-1",
    )
    event_queue = EventQueueLegacy()
    task_store = InMemoryTaskStore()

    context = A2ATurnContext(
        adapter,
        MagicMock(spec=AgentApplication),
        activity,
        identity,
        request_context=request_context,
        event_queue=event_queue,
        task_store=task_store,
    )

    assert context.adapter is adapter
    assert context.activity is activity
    assert isinstance(context.activity, A2AActivity)
    assert context.identity is identity
    assert context.client.request_context is request_context
    assert context.client.event_queue is event_queue
    assert context.client.task_store is task_store


def test_responded_property_is_forwarded_to_original_context():
    original = _original_context()
    context = A2ATurnContext.from_existing(
        original,
        MagicMock(spec=AgentApplication),
    )

    context.responded = True

    assert original.responded is True
    assert context.responded is True


def test_streaming_response_is_forwarded_to_original_context():
    original = _original_context()
    context = A2ATurnContext.from_existing(
        original,
        MagicMock(spec=AgentApplication),
    )

    assert context.streaming_response is original.streaming_response

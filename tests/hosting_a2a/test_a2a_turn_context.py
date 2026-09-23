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
    context = A2ATurnContext(original, MagicMock(spec=AgentApplication))

    assert isinstance(context.activity, A2AActivity)
    assert context.activity.text == "hello"
    assert context.client.event_queue is original.services.get(EventQueue)
    assert context.client.request_context is original.services.get(RequestContext)
    assert context.client.task_store is original.services.get(TaskStore)


def test_responded_property_is_forwarded_to_original_context():
    original = _original_context()
    context = A2ATurnContext(original, MagicMock(spec=AgentApplication))

    context.responded = True

    assert original.responded is True
    assert context.responded is True


def test_streaming_response_is_forwarded_to_original_context():
    original = _original_context()
    context = A2ATurnContext(original, MagicMock(spec=AgentApplication))

    assert context.streaming_response is original.streaming_response

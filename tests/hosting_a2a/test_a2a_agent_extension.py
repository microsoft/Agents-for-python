# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue, EventQueueLegacy
from a2a.server.tasks import InMemoryTaskStore, TaskStore

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import ChannelAdapter, ClaimsIdentity, TurnContext
from microsoft_agents.hosting.a2a.a2a_agent_extension import A2AAgentExtension
from microsoft_agents.hosting.a2a.a2a_turn_context import A2ATurnContext


class _Adapter(ChannelAdapter):
    async def send_activities(self, context, activities):
        return []

    async def update_activity(self, context, activity):
        return None

    async def delete_activity(self, context, reference):
        return None


class _RecordingApplication:
    def message(self, select, *, auth_handlers=None, **kwargs):
        self.registration = (select, auth_handlers, kwargs)

        def register(handler):
            self.handler = handler
            return handler

        return register


def _turn_context():
    context = TurnContext(
        _Adapter(),
        Activity(type="message", text="hello"),
        ClaimsIdentity(),
    )
    context.services.set(EventQueue, EventQueueLegacy())
    context.services.set(
        RequestContext,
        RequestContext(
            ServerCallContext(),
            task_id="task-1",
            context_id="context-1",
        ),
    )
    context.services.set(TaskStore, InMemoryTaskStore())
    return context


@pytest.mark.asyncio
async def test_message_handler_receives_a2a_context_and_registration_options():
    app = _RecordingApplication()
    extension = A2AAgentExtension(app)
    handler = AsyncMock()

    registered_handler = extension.message(
        ["hello", "help"],
        auth_handlers=["auth"],
        rank=10,
    )(handler)
    state = object()

    await registered_handler(_turn_context(), state)

    assert app.registration == (["hello", "help"], ["auth"], {"rank": 10})
    context = handler.call_args.args[0]
    assert isinstance(context, A2ATurnContext)
    assert context.activity.text == "hello"
    assert handler.call_args.args[1] is state


@pytest.mark.asyncio
async def test_message_handler_reuses_existing_a2a_context():
    app = _RecordingApplication()
    extension = A2AAgentExtension(app)
    handler = AsyncMock()
    registered_handler = extension.message([])(handler)
    context = A2ATurnContext(_turn_context(), app)
    state = object()

    await registered_handler(context, state)

    assert handler.call_args.args == (context, state)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue, EventQueueLegacy
from a2a.server.tasks import InMemoryTaskStore, TaskStore

from microsoft_agents.hosting.a2a.a2a_client import A2AClient


class _Services:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values.get(key)


def _services():
    event_queue = EventQueueLegacy()
    request_context = RequestContext(
        ServerCallContext(),
        task_id="task-1",
        context_id="context-1",
    )
    task_store = InMemoryTaskStore()
    return {
        EventQueue: event_queue,
        RequestContext: request_context,
        TaskStore: task_store,
    }


def test_client_exposes_services_from_turn_context():
    services = _services()
    client = A2AClient(SimpleNamespace(services=_Services(services)))

    assert client.event_queue is services[EventQueue]
    assert client.request_context is services[RequestContext]
    assert client.task_store is services[TaskStore]


@pytest.mark.parametrize("missing_service", [EventQueue, RequestContext, TaskStore])
def test_client_requires_all_services(missing_service):
    services = _services()
    del services[missing_service]

    with pytest.raises(ValueError, match="Missing required services"):
        A2AClient(SimpleNamespace(services=_Services(services)))

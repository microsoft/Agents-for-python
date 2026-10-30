# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.server.events import EventQueue
from a2a.server.agent_execution import RequestContext
from a2a.server.tasks import TaskStore

from microsoft_agents.hosting.core import TurnContext


class A2AClient:
    """A client for interacting with the A2A services within a TurnContext."""

    def __init__(self, context: TurnContext):
        """Initialize the A2AClient with the given TurnContext.

        :param context: The TurnContext containing the required services.
        """

        event_queue = context.services.get(EventQueue)
        request_context = context.services.get(RequestContext)
        task_store = context.services.get(TaskStore)

        if not event_queue or not request_context or not task_store:
            raise ValueError("Missing required services in TurnContext.")

        self._event_queue = event_queue
        self._request_context = request_context
        self._task_store = task_store

    @property
    def event_queue(self) -> EventQueue:
        """Get the event queue associated with this client."""
        return self._event_queue

    @property
    def request_context(self) -> RequestContext:
        """Get the request context associated with this client."""
        return self._request_context

    @property
    def task_store(self) -> TaskStore:
        """Get the task store associated with this client."""
        return self._task_store

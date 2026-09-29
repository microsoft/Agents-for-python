# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import cast

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskStore

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    ChannelAdapter,
    ClaimsIdentity,
)

from .activity import A2AActivity
from .a2a_client import A2AClient


class A2ATurnContext(TurnContext):
    """A context object for handling A2A-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Teams-aware route handlers
    receive a typed context without changing the core routing engine.
    """

    def __init__(
        self,
        adapter: ChannelAdapter,
        app: AgentApplication,
        activity: Activity,
        identity: ClaimsIdentity,
        *,
        request_context: RequestContext,
        event_queue: EventQueue,
        task_store: TaskStore,
    ) -> None:
        """Initialize the A2A turn context with the given adapter, app, activity, and identity.

        :param adapter: The channel service adapter.
        :param app: The agent application instance.
        :param activity: The activity for the turn context.
        :param identity: The claims identity for the turn context.
        """
        super().__init__(adapter, activity, identity)

        self._original = self
        self._app = app
        self._activity.__class__ = A2AActivity
        self._a2a_activity = cast(A2AActivity, self._activity)

        self._services.set(RequestContext, request_context)
        self._services.set(EventQueue, event_queue)
        self._services.set(TaskStore, task_store)

        self._client = A2AClient(self)

    @staticmethod
    def from_existing(
        context: TurnContext,
        app: AgentApplication,
    ) -> A2ATurnContext:
        """Initialize the A2A turn context.

        :param context: The existing turn context.
        :param app: The agent application instance.
        :return: An instance of A2ATurnContext.
        """

        obj = A2ATurnContext.__new__(A2ATurnContext)

        super(A2ATurnContext, obj).__init__(context)

        obj._original = context
        obj._turn_state = context.turn_state
        obj._app = app
        obj._activity.__class__ = A2AActivity
        obj._a2a_activity = cast(A2AActivity, obj._activity)
        obj._client = A2AClient(obj)

        return obj

    @property
    def client(self) -> A2AClient:
        """Get the A2A client associated with this turn context."""
        return self._client

    @property
    def responded(self) -> bool:
        """Check if the turn context has already sent a response."""
        return self._original._responded

    @responded.setter
    def responded(self, value: bool):
        """Set the responded status for the turn context."""
        self._original._responded = value

    @property
    def streaming_response(self):
        """Get the streaming response associated with the turn context."""
        if self._original is self:
            return super().streaming_response
        return self._original.streaming_response

    @property
    def activity(self) -> A2AActivity:
        """Get the A2A activity associated with the turn context."""
        return self._a2a_activity

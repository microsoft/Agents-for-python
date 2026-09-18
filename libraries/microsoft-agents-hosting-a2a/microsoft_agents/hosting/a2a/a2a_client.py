from a2a.server.events import EventQueue
from a2a.server.agent_execution import RequestContext
from a2a.server.tasks import TaskStore

from microsoft_agents.hosting.core import TurnContext


class A2AClient:

    def __init__(self, context: TurnContext):

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
        return self._event_queue

    @property
    def request_context(self) -> RequestContext:
        return self._request_context

    @property
    def task_store(self) -> TaskStore:
        return self._task_store

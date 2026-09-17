# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TYPE_CHECKING
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue

from fastapi import Request


from microsoft_agents.hosting.core import (
    Agent,
    ClaimsIdentity
)

if TYPE_CHECKING:
    from .a2a_adapter import A2AAdapter

class AgentRequestContext(AgentExecutor):

    def __init__(self, request: Request, adapter: "A2AAdapter", agent: Agent):

        self._adapter = adapter
        self._agent = agent
        self._identity = ClaimsIdentity() # TODO!
        self._event_queue: EventQueue | None = None
        self._request_id = request.headers.get("X-Request-ID") or uuid4() # TODO!

    @property
    def adapter(self) -> "A2AAdapter":
        return self._adapter

    @property
    def agent(self) -> Agent:
        return self._agent

    @property
    def identity(self) -> ClaimsIdentity:
        return self._identity

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        self._event_queue = event_queue
        # if not context.is_continuation

        # task_updater = context.task_updater

        await self._adapter.execute_agent_turn(self._request_id, self._identity, self._agent, context, event_queue)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
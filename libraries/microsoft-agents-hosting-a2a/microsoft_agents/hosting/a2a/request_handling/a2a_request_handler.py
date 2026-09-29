# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.types import AgentCard, SubscribeToTaskRequest

from a2a.server.tasks import TaskStore
from a2a.server.request_handlers import DefaultRequestHandlerV2
from a2a.utils.errors import (
    TaskNotFoundError,
    UnsupportedOperationError,
)
from a2a.server.context import ServerCallContext
from a2a.server.agent_execution.active_task import TERMINAL_TASK_STATES

from .a2a_http_adapter import A2AHttpAdapter

from .a2a_agent_executor import A2AAgentExecutor


class A2ARequestHandler(DefaultRequestHandlerV2):
    """Request handler for A2A interactions."""

    def __init__(
        self,
        adapter: A2AHttpAdapter,
        task_store: TaskStore,
        agent_card: AgentCard,
    ):
        self._adapter = adapter
        super().__init__(A2AAgentExecutor(self._adapter), task_store, agent_card)

    def update_agent_card(self, agent_card: AgentCard) -> None:
        """Update the agent card with the provided AgentCard instance.

        :param agent_card: The AgentCard instance to update the handler with.
        """
        self._agent_card = agent_card

    async def on_subscribe_to_task(self, params: SubscribeToTaskRequest, context: ServerCallContext):
        """Handle subscription to a task.

        :param params: The parameters for the subscription request.
        :param context: The context of the request.
        :raises TaskNotFoundError: If the task does not exist.
        :raises UnsupportedOperationError: If the task is in a terminal state.
        :yield: Events related to the task subscription.
        """
        task = await self.task_store.get(params.id, context)
        if task is None:
            raise TaskNotFoundError()

        if task.status.state in TERMINAL_TASK_STATES:
            raise UnsupportedOperationError(
                "Cannot subscribe to a terminal task."
            )

        async for event in super().on_subscribe_to_task(params, context):
            yield event
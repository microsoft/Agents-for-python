# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams Task Module route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models import TaskModuleRequest, TaskModuleResponse

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT


class FetchHandler(Protocol[StateT]):
    """Protocol for a handler invoked on task/fetch activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        request: TaskModuleRequest,
    ) -> Awaitable[TaskModuleResponse]:
        """Handle a task module fetch invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param request: The parsed task module request payload.
        :return: A task module response describing the UI to display.
        """
        ...


class SubmitHandler(Protocol[StateT]):
    """Protocol for a handler invoked on task/submit activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        request: TaskModuleRequest,
    ) -> Awaitable[TaskModuleResponse]:
        """Handle a task module submit invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param request: The parsed task module request payload containing user input.
        :return: A task module response (e.g. a message or a follow-up task module).
        """
        ...

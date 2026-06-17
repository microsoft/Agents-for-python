from typing import Awaitable, Protocol

from microsoft_teams.api.models import (
    TaskModuleRequest,
    TaskModuleResponse
)

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class TaskFetchHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            request: TaskModuleRequest,
        ) -> Awaitable[TaskModuleResponse]:
        ...

class TaskSubmitHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            request: TaskModuleRequest,
        ) -> Awaitable[TaskModuleResponse]:
        ...
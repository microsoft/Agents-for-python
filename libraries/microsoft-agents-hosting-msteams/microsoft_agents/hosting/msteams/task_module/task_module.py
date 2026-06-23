# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams Task Module (task/fetch, task/submit) invokes."""

from typing import Any, Generic, Optional

from microsoft_teams.api.models.task_module import TaskModuleRequest

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import AgentApplication, RouteRank, TurnContext

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    CommandSelector,
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.msteams._utils import (
    _match_selector,
    _send_invoke_response,
)

from .route_handlers import FetchHandler, SubmitHandler


class TaskModule(Generic[StateT]):
    """
    Route registration for Teams Task Module (task/fetch, task/submit) invoke activities.
    Access via TeamsAgentExtension.task_modules.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    @staticmethod
    def _get_verb(value: Optional[Any]) -> Optional[str]:
        """Extract the verb from a task module request payload.

        :param value: The raw activity value (expected to be a dict with a ``data`` sub-dict).
        :return: The verb string if present, otherwise None.
        """
        if not isinstance(value, dict):
            return None
        data = value.get("data")
        if isinstance(data, dict):
            return data.get("verb")
        return None

    def fetch(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[FetchHandler[StateT]]:
        """Register a handler for task/fetch invokes.

        :param verb: Optional verb string or regex to match against task data.
            If None, matches all task/fetch invokes.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "task/fetch"
            ):
                return False
            return _match_selector(verb, TaskModule._get_verb(context.activity.value))

        def __call(func: FetchHandler[StateT]) -> FetchHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(teams_context, state, request)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def submit(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[SubmitHandler[StateT]]:
        """Register a handler for task/submit invokes.

        :param verb: Optional verb string or regex to match against task data.
            If None, matches all task/submit invokes.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "task/submit"
            ):
                return False
            return _match_selector(verb, TaskModule._get_verb(context.activity.value))

        def __call(func: SubmitHandler[StateT]) -> SubmitHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(teams_context, state, request)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

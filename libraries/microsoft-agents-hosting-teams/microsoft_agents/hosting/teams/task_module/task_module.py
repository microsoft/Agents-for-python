from typing import (
    Any,
    Generic,
    Optional
)

from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext
)

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams._type_defs import (
    CommandSelector,
    RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.teams._utils import (
    _match_selector,
    _send_invoke_response,
)

from .route_handlers import (
)

class TaskModule(Generic[StateT]):
    """
    Route registration for Teams Task Module (task/fetch, task/submit) invoke activities.
    Access via TeamsAgentExtension.task_module.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    @staticmethod
    def _get_verb(value: Optional[Any]) -> Optional[str]:
        if not isinstance(value, dict):
            return None
        data = value.get("data")
        if isinstance(data, dict):
            return data.get("verb")
        return None

    def on_fetch(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> RouteDecorator[]:
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

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(context, state, request)
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

    def on_submit(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
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

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(context, state, request)
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
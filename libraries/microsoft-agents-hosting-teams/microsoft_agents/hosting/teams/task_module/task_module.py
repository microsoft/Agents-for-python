from re import S
from typing import Optional, Union
from enum import Enum
from unittest.mock import DEFAULT

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    INVOKE_RESPONSE_KEY,
    InvokeResponse,
    RouteHandler,
    RouteSelector,
    TurnContext,
    TurnState
)
from .models import TaskModuleTaskInfo, TaskModuleResponse

class TaskModuleInvokeNames(str, Enum):
    CONFIG_FETCH_INVOKE_NAME = "config/fetch"
    CONFIG_SUBMIT_INVOKE_NAME = "config/submit"
    FETCH_INVOKE_NAME = "task/fetch"
    SUBMIT_INVOKE_NAME = "task/submit"
    DEFAULT_TASK_DATA_FILTER = "verb"

class TaskModuleOptions:
    task_data_filter: Optional[str]

Verb = TypeVar("Verb", bound=Union[str, RouteSelector])

def create_task_selector(verb: Verb, filter_field: str, invoke_name: str) -> RouteSelector:
    if isinstance(verb, RouteSelector):
        return verb
    
    if isinstance(verb, Pattern):
        async def route_selector(context: TurnContext) -> bool:
            is_teams = context.activity.channel_id == MS_TEAMS
            is_invoke = context.activity.type == ActivityTypes.invoke and context.activity.name == invoke_name
            data = context.activity.value.get("data", {})
            if is_invoke and is_team and isinstance(data, dict) and isinstance(data.get("filter_field"), str):
                return verb.match(data["filter_field"]) is not None
            return False
    else:
        async def route_selector(context: TurnContext) -> bool:
            is_invoke = context.activity.type == ActivityTypes.invoke and context.activity.name == invoke_name
            data = context.activity.value.get("data", {})
            return is_invoke and isinstance(data, dict) and data.get(filter_field) == verb
        
    return route_selector

class TaskModule:
    
    def __init__(self, options: TaskModuleOptions = None):
        self._app = None
        self._options = options or TaskModuleOptions(TaskModuleInvokeNames.DEFAULT_TASK_DATA_FILTER)

    def _base_route_selector(self, invoke_name_category: str) -> RouteSelector:
        activity_name = f"task/{invoke_name_category}"
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.invoke and \
                context.activity.channel_id == MS_TEAMS and \
                context.activity.name == activity_name
        return route_selector
    
    def on_fetch(self, handler: RouteHandler) -> RouteHandler:
        route_selector = self._base_route_selector("fetch")
        return self._app.add_route(route_selector, handler, True)
    
    def _submit(self, verb: Verb, handler: RouteHandler) -> AgentApplication:
        filter_field = self._options.task_data_filter or TaskModuleInvokeNames.DEFAULT_TASK_DATA_FILTER
        selector = create_task_selector(verb, filter_field, TaskModuleInvokeNames.SUBMIT_INVOKE_NAME)
        
        async def route_handler(context: TurnContext, state: UserState):
            if context.activity.channel_id == MS_TEAMS:
                if context.activity.type != ActivityTypes.invoke or context.activity.name != TaskModuleInvokeNames.SUBMIT_INVOKE_NAME:
                    raise Exception(f"Unexpected TaskModule.submit() triggered for activity type: {context.activity.type}")
            
            result = await handler(context, state, context.activity.value.data or dict())

            if not result:
                await context.send_activity(Activity(
                    value=InvokeResponse(status=200),
                    type=ActivityTypes.invoke_response,
                ))

            if not context.turn_state.get(INVOKE_RESPONSE_KEY):
                response = None
                if isinstance(result, str):
                    response = TaskModuleResponse(type="message", value=result)
                elif isinstance(result, dict):
                    response = TaskModuleResponse(type="continue", value=TaskModuleTaskInfo(result))
                
                await context.send_activity(Activity(
                    value=InvokeResponse(status=200, body=response),
                    type=ActivityTypes.invoke_response
                ))

        return self._app.add_route(selector, route_handler, True)

    
    def submit(
        self,
        verb: Union[Verb, list[Verb]],
        handler: Awaitable[[TurnContext, TState, TData], Union[TaskModuleInfo, str, None]]
    ) -> AgentApplication:
        if isinstance(verb, list):
            for v in verb:
                self._submit(v, handler)

    def _on_task_module_invoke(self, invoke_name: str, handler: RouteHandler, verb: str = None) -> RouteHandler:
        if verb:
            async def route_selector(context: TurnContext) -> bool:
                return context.activity.type == ActivityTypes.invoke and \
                    context.activity.channel_id == MS_TEAMS and \
                    context.activity.name == invoke_name and \
                    context.activity.value.data == verb
        else:
            async def route_selector(context: TurnContext) -> bool:
                return context.activity.type == ActivityTypes.invoke and \
                    context.activity.channel_id == MS_TEAMS and \
                    context.activity.name == invoke_name
        return self._app.add_route(route_selector, handler, True)

    def on_fetch_by_verb(self, verb: str, handler: RouteHandler) -> RouteHandler:
        return self._on_task_module_invoke(TaskModuleInvokeNames.FETCH_INVOKE_NAME, handler, verb)
    
    def on_submit_by_verb(self, verb: str, handler: RouteHandler) -> RouteHandler:
        return self._on_task_module_invoke(TaskModuleInvokeNames.SUBMIT_INVOKE_NAME, handler, verb)
    
    def on_configuration_fetch(self, handler: RouteHandler) -> RouteHandler:
        return self._on_task_module_invoke(TaskModuleInvokeNames.CONFIG_FETCH_INVOKE_NAME, handler)
    
    def on_configuration_submit(self, handler: RouteHandler) -> RouteHandler:
        return self._on_task_module_invoke(TaskModuleInvokeNames.CONFIG_SUBMIT_INVOKE_NAME, handler)
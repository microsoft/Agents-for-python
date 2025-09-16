from typing import Optional
from enum import Enum

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

class TaskModule:
    
    def __init__(self, options: TaskModuleOptions = None):
        self._app = None
        self._options = options or TaskModuleOptions(TaskModuleInvokeNames.DEFAULT_TASK_DATA_FILTER)

    def _base_route_selector(self, invoke_name_category: str) -> RouteSelector:
        activity_name = f"task/{invoke_name_category}"
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.invoke and
                context.activity.channel_id == MS_TEAMS and
                context.activity.name == activity_name
        return route_selector
    
    def on_fetch(self, handler: RouteHandler) -> RouteHandler:
        route_selector = self._base_route_selector("fetch")
        return self._app.add_route(route_selector, handler, True)
    
    def submit(
        self,
        verb: Union[str, RegExp, RouteSelector, ]
    )
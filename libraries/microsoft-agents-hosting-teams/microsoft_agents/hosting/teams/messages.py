from enum import Enum
from typing import Awaitable, TypeVar, Union

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels
)

from microsoft_agents.hosting.core import (
    AgentApplication,
    INVOKE_RESPONSE_KEY,
    InvokeResponse,
    TurnContext,
    TurnState
)
from .task_module import (
    TaskModuleResponse,
    TaskModuleTaskInfo
)

class MessageInvokeNames(str, Enum):
    FETCH_INVOKE_NAME = "message/fetchTask"

MessageHandler = TypeVar(
    "MessageHandler",
    bound=Awaitable[[TurnContext, TurnState, TData], Union[TaskModuleTaskInfo, str]]
)

class Messages:

    def __init__(self):
        self._app = None

    @staticmethod
    async def route_selector(context: TurnContext) -> bool:
        return (
            context.activity.type == ActivityTypes.INVOKE and
            context.activity.name == MessageInvokeNames.FETCH_INVOKE_NAME
        )
    
    @staticmethod
    async def middleware(handler: MessageHandler) -> None:
        async def func(context: TurnContext, state: TurnState) -> None:
            if context.activity.channel_id == MS_TEAMS:
                result = await handler(context, state, context.activity.value).data or {}
                if not context.turn_state.get(INVOKE_RESPONSE_KEY):
                    response = TaskModuleResponse(
                        type="message" if isinstance(result, str) else "continue",
                        value=result
                    )
                await context.send_activity(Activity(
                    value=InvokeResponse(
                        body=response,
                        status=200
                    ),
                    type=ActivityTypes.invoke_response
                ))
        return func

    def fetch(self, handler: MessageHandler) -> AgentApplication:
        self._app.add_route(
            Messages.route_selector,
            Messages.middleware(handler),
            True
        )
        return self._app
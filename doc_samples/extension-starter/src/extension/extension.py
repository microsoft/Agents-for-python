from venv import create

from typing import (
    Awaitable,
    Generic,
    TypeVar
)

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    InvokeResponse
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
)

from src.extension.custom_event_data import CustomEventData
from src.extension.custom_event_result import CustomEventResult
from src.extension.custom_event_types import CustomEventTypes

TState = TypeVar("TState", bound=TurnState)
CustomRouteHandler = TypeVar("CustomRouteHandler",
    bound=Awaitable[[TurnContext, TState, CustomEventData], CustomEventResult])

def create_route_selector(event_name: str) -> Awaitable[[TurnContext], bool]:

    async def route_selector(context: TurnContext) -> bool:
        return context.activity.type == ActivityTypes.message and \
            context.activity.channel_id == MY_CHANNEL and \
            context.activity.name == f"invoke/{event_name}"

    return route_selector   

class ExtensionAgent(Generic[TState]):

    def __init__(self, app: AgentApplication):
        self.app = app

    def on_invoke_custom_event(self, handler: RouteQueryHandler[TState]):
        route_selector = create_route_selector(CustomEventTypes.CUSTOM_EVENT)
        async def route_handler(context: TurnContext, state: TState):
            custom_event_data = CustomEventData.from_context(context)
            result = await handler(context, state, custom_event_data)
            if not result:
                result = CustomEventResult()

            response = Activity(type=ActivityTypes.invoke_response, value=InvokeResponse(
                status=200,
                body=result
            ))
            await context.send_activity(response)
        self.app.add_route(route_selector, route_handler, True)

    def on_invoke_other_custom_event(self, handler: RouteHandler[TState]):
        route_selector = create_route_selector(CustomEventTypes.OTHER_CUSTOM_EVENT)
        async def route_handler(context: TurnContext, state: TState):
            await handler(context, state)
            response = Activity(type=ActivityTypes.invoke_response, value=InvokeResponse(
                status=200,
                body={}
            ))
            await context.send_activity(response)
        self.app.add_route(route_selector, route_handler, True)

    def on_message_reaction_added(self, handler: Awaitable[[TurnContext, TState, str], None]):

        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.message and \
                context.activity.name == "reactionAdded"
    
        async def route_handler(context: TurnContext, state: TState):
            reactions_added = context.activity.reactions_added
            for reaction in context.activity.values:
                await handler(context, state, reaction.type)

        self.app.add_route(route_selector, route_handler)
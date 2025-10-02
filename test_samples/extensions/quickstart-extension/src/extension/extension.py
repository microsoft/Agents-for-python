import logging
from typing import (
    Awaitable,
    Callable,
    Generic,
    TypeVar,
)

from microsoft_agents.activity import Activity, ActivityTypes, InvokeResponse
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
    RouteSelector,
)

logger = logging.getLogger(__name__)

MY_CHANNEL = "mychannel"

from .models import (
    CustomEventData,
    CustomEventResult,
    CustomEventTypes,
    CustomRouteHandler,
)


def create_route_selector(event_name: str) -> RouteSelector:

    async def route_selector(context: TurnContext) -> bool:
        return (
            context.activity.type == ActivityTypes.message
            and context.activity.channel_id == MY_CHANNEL
            and context.activity.name == f"invoke/{event_name}"
        )

    return route_selector


class ExtensionAgent(Generic[StateT]):
    app: AgentApplication[StateT]

    def __init__(self, app: AgentApplication[StateT]):
        self.app = app

    def on_invoke_custom_event(self, handler: CustomRouteHandler[StateT]):
        route_selector = create_route_selector(CustomEventTypes.CUSTOM_EVENT)

        async def route_handler(context: TurnContext, state: StateT):
            custom_event_data = CustomEventData.from_context(context)
            result = await handler(context, state, custom_event_data)
            if not result:
                result = CustomEventResult()

            response = Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(status=200, body=result),
            )
            await context.send_activity(response)

        logger.debug("Registering route for custom event")
        self.app.add_route(route_selector, route_handler, is_invoke=True)

    def on_invoke_other_custom_event(self, handler: RouteHandler[StateT]):
        route_selector = create_route_selector(CustomEventTypes.OTHER_CUSTOM_EVENT)

        async def route_handler(context: TurnContext, state: StateT):
            await handler(context, state)
            response = Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(status=200, body={}),
            )
            await context.send_activity(response)

        logger.debug("Registering route for other custom event")
        self.app.add_route(route_selector, route_handler, is_invoke=True)

    # Callable that takes in three arguments (TurnContext, StateT, str) and returns Awaitable[None]
    # Awaitable indicates that the function is asynchronous and returns a coroutine
    def on_message_reaction_added(
        self, handler: Callable[[TurnContext, StateT, str], Awaitable[None]]
    ):

        async def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and context.activity.name == "reactionAdded"
            )

        async def route_handler(context: TurnContext, state: StateT):
            reactions_added = context.activity.reactions_added
            for reaction in context.activity.value:
                await handler(context, state, reaction.type)

        logger.debug("Registering route for message reaction added")
        self.app.add_route(route_selector, route_handler)

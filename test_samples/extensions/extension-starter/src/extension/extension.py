import logging
from typing import Awaitable, Callable, Generic, TypeVar

from microsoft_agents.activity import Activity, ActivityTypes, InvokeResponse
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
    RouteHandler,
)

from .models import (
    CustomEventData,
    CustomEventResult,
    CustomEventTypes,
    CustomRouteHandler,
)

logger = logging.getLogger(__name__)

MY_CHANNEL = "mychannel"


StateT = TypeVar("StateT", bound=TurnState)


class ExtensionAgent(Generic[StateT]):
    app: AgentApplication[StateT]

    def __init__(self, app: AgentApplication[StateT]):
        self.app = app

    # defining event decorators with custom selectors
    # allowing event decorators to accept **kwargs and passing
    # **kwargs to app.add_route is recommended
    def _on_message_has_hello_event(
        self,
        handler: Callable[[TurnContext, StateT, CustomEventData], Awaitable[None]],
        **kwargs,
    ):
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and "hello" in context.activity.text.lower()
            )

        async def route_handler(context: TurnContext, state: StateT):
            custom_event_data = CustomEventData.from_context(context)
            await handler(context, state, custom_event_data)

        logger.debug("Registering route for message has hello event")
        self.app.add_route(route_selector, route_handler, **kwargs)

    def on_message_has_hello_event(
        self,
        handler: Callable[[TurnContext, StateT, CustomEventData], Awaitable[None]],
        **kwargs,
    ):
        self._on_message_has_hello_event(handler, is_agentic=False, **kwargs)

    def on_agentic_message_has_hello_event(
        self,
        handler: Callable[[TurnContext, StateT, CustomEventData], Awaitable[None]],
        **kwargs,
    ):
        self._on_message_has_hello_event(handler, is_agentic=True, **kwargs)

    # events that are handled with custom payloads
    def on_invoke_custom_event(self, handler: CustomRouteHandler[StateT], **kwargs):
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and context.activity.channel_id == MY_CHANNEL
                and context.activity.name == f"invoke/{CustomEventTypes.CUSTOM_EVENT}"
            )

        async def route_handler(context: TurnContext, state: StateT):
            custom_event_data = CustomEventData.from_context(context)
            result = await handler(context, state, custom_event_data)
            if not result:
                result = CustomEventResult()

            # send an invoke response back to the caller
            # invokes must send back an invoke response
            response = Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(status=200, body=result),
            )
            await context.send_activity(response)

        logger.debug("Registering route for custom event")
        self.app.add_route(route_selector, route_handler, is_invoke=True, **kwargs)

    # event that does not require a custom payload
    def on_invoke_other_custom_event(self, handler: RouteHandler[StateT], **kwargs):
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and context.activity.channel_id == MY_CHANNEL
                and context.activity.name
                == f"invoke/{CustomEventTypes.OTHER_CUSTOM_EVENT}"
            )

        async def route_handler(context: TurnContext, state: StateT):
            await handler(context, state)

            # send an invoke response back to the caller
            # invokes must send back an invoke response
            response = Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(status=200, body={}),
            )
            await context.send_activity(response)

        logger.debug("Registering route for other custom event")
        self.app.add_route(route_selector, route_handler, is_invoke=True, **kwargs)

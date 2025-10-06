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

# This extension defines event decorators with custom selecting/handling logic:
class ExtensionAgent(Generic[StateT]):
    app: AgentApplication[StateT]

    def __init__(self, app: AgentApplication[StateT]):
        self.app = app

    # Allowing event decorators to accept **kwargs and passing
    # **kwargs to app.add_route is recommended.
    def _on_message_has_hello_event(
        self, **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and "hello" in context.activity.text.lower()
            )

        def create_handler(handler: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            async def route_handler(context: TurnContext, state: StateT):
                custom_event_data = CustomEventData.from_context(context)
                await handler(context, state, custom_event_data)
            return route_handler

        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for message has hello event")
            handler = create_handler(func)
            self.app.add_route(route_selector, handler, **kwargs)
            return handler

        return __call

    def on_message_has_hello_event(
        self, **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        return self._on_message_has_hello_event(is_agentic=False, **kwargs)

    def on_agentic_message_has_hello_event(
        self, **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        return self._on_message_has_hello_event(is_agentic=True, **kwargs)

    # events that are handled with custom payloads
    def on_invoke_custom_event(self, custom_event_type: str, **kwargs) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and context.activity.channel_id == MY_CHANNEL
                and context.activity.name == f"invoke/{custom_event_type}"
            )

        def create_handler(handler: CustomRouteHandler) -> RouteHandler[StateT]:
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
            return route_handler

        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for custom event")
            handler = create_handler(func)
            self.app.add_route(route_selector, handler, is_invoke=True, **kwargs)
            return handler

        return __call
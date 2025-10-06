import logging
from typing import Callable, Generic, TypeVar

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
    CustomRouteHandler,
)

logger = logging.getLogger(__name__)

MY_CHANNEL = "mychannel"

StateT = TypeVar("StateT", bound=TurnState)


# This extension defines event decorators with custom selecting/handling logic:
class ExtensionAgent(Generic[StateT]):
    """An extension agent that provides custom event decorators."""

    app: AgentApplication[StateT]

    def __init__(self, app: AgentApplication[StateT]):
        """Initialize the ExtensionAgent with an AgentApplication.

        :param app: The AgentApplication instance to extend.
        """
        self.app = app

    # Allowing event decorators to accept **kwargs and passing
    # **kwargs to app.add_route is recommended.
    def _on_message_has_hello_event(
        self,
        **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        """Decorator for message activities that contain the word 'hello'.

        This demonstrates a custom event selector and handler that extracts
        additional data from the activity and passes it to the handler.

        :param kwargs: Additional keyword arguments to pass to app.add_route.
        :return: A decorator that registers the route handler.

        Usage:
            @extension_agent.on_message_has_hello_event()
            async def handle_hello_event(context: TurnContext, state: StateT, event_data: CustomEventData):
                await context.send_activity(f"Hello! You said: {event_data.text}")
        """

        # the function the AgentApplication uses to determine if this route should be called
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message
                and "hello" in context.activity.text.lower()
            )

        # the function that wraps the user's handler to extract custom data
        def create_handler(handler: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            async def route_handler(context: TurnContext, state: StateT):
                custom_event_data = CustomEventData.from_context(context)
                await handler(context, state, custom_event_data)

            return route_handler

        # the decorator that registers the route handler with the app
        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for message has hello event")
            handler = create_handler(func)
            self.app.add_route(route_selector, handler, **kwargs)
            return handler

        return __call

    def on_message_has_hello_event(
        self,
        **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        """Decorator for non-agentic message activities that contain the word 'hello'."""
        return self._on_message_has_hello_event(is_agentic=False, **kwargs)

    def on_agentic_message_has_hello_event(
        self,
        **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        """Decorator for agentic message activities that contain the word 'hello'."""
        return self._on_message_has_hello_event(is_agentic=True, **kwargs)

    # events that are handled with custom payloads
    def on_invoke_custom_event(
        self, custom_event_type: str, **kwargs
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        """Decorator for invoke activities with a specific custom event type.

        This demonstrates a custom event selector and handler that extracts
        additional data from the activity and passes it to the handler.

        :param custom_event_type: The custom event type to listen for.
        :param kwargs: Additional keyword arguments to pass to app.add_route.
        :return: A decorator that registers the route handler.
        Usage:
            @extension_agent.on_invoke_custom_event("my_custom_event")
            async def handle_custom_event(context: TurnContext, state: StateT, event_data: CustomEventData):
                await context.send_activity(f"Received custom event with data: {event_data.data}")
                return CustomEventResult(success=True)
        """

        # the function the AgentApplication uses to determine if this route should be called
        def route_selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.channel_id == MY_CHANNEL
                and context.activity.name == f"invoke/{custom_event_type}"
            )

        # the function that wraps the user's handler to extract custom data
        # it also sends back an invoke response with the handler's result
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
                    value=InvokeResponse(
                        status=200, body=result.model_dump(mode="json")
                    ),
                )
                await context.send_activity(response)

            return route_handler

        # the decorator that registers the route handler with the app
        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for custom event")
            handler = create_handler(func)
            self.app.add_route(route_selector, handler, is_invoke=True, **kwargs)
            return handler

        return __call

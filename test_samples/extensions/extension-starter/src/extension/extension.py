import logging
import re
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

    # Forward route options to the application's decorators.
    def _on_message_has_hello_event(
        self,
        **kwargs,
    ) -> Callable[[CustomRouteHandler[StateT]], RouteHandler[StateT]]:
        """Decorator for message activities that contain the word 'hello'.

        This uses the application's regex message selector and wraps the handler
        to extract additional data from the activity.

        :param kwargs: Additional keyword arguments to pass to app.message.
        :return: A decorator that registers the route handler.

        Usage:
            @extension_agent.on_message_has_hello_event()
            async def handle_hello_event(context: TurnContext, state: StateT, event_data: CustomEventData):
                await context.send_activity(f"Hello! User ID: {event_data.user_id}")
        """

        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for message has hello event")

            @self.app.message(
                re.compile(r".*hello.*", re.IGNORECASE | re.DOTALL), **kwargs
            )
            async def route_handler(context: TurnContext, state: StateT):
                custom_event_data = CustomEventData.from_context(context)
                await func(context, state, custom_event_data)

            return route_handler

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

        This uses the application's channel-scoped invoke selector and wraps
        the handler to extract custom data and send an invoke response.

        :param custom_event_type: The custom event type to listen for.
        :param kwargs: Additional keyword arguments to pass to app.invoke.
        :return: A decorator that registers the route handler.
        Usage:
            @extension_agent.on_invoke_custom_event("my_custom_event")
            async def handle_custom_event(context: TurnContext, state: StateT, event_data: CustomEventData):
                return CustomEventResult(user_id=event_data.user_id, field=event_data.field)
        """

        def __call(func: CustomRouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug("Registering route for custom event")

            @self.app.invoke(
                f"invoke/{custom_event_type}", channel_id=MY_CHANNEL, **kwargs
            )
            async def route_handler(context: TurnContext, state: StateT):
                custom_event_data = CustomEventData.from_context(context)
                result = await func(context, state, custom_event_data)
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

        return __call

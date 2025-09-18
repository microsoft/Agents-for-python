from microsoft_agents.activity import (
    Activity,
    AgentsModel
)

from microsoft_agents.hosting.core import (
    TurnState,
    TurnContext
)

TState = TypeVar("TState", bound=TurnState)
RouteQueryHandler = TypeVar("RouteQueryHandler",
    bound=Awaitable[[TurnContext, TState, query: ExtensionQuery], ExtensionResult])

def create_route_selector(route_type: str) -> Awaitable[[TurnContext], bool]:

    async def route_selector(context: TurnContext) -> bool:
        return context.activity.type == ActivityTypes.message and \
            context.activity.channel_id == MY_CHANNEL and \
            context.activity.name == route_type

    return route_selector   

class MessageExtension(Generic[TState]):

    def __init__(self, app: AgentApplication):
        self._app = app
    
    def on_query(self, handler: RouteQueryHandler[TState]):

        route_selector = create_route_selector("query")

        async def route_handler(context: TurnContext, state: TState):
            message_extension_query = MessageExtensionQuery.model_validate(context.activity.value)
            result = await handler(context, state, message_extension_query)
        
        self._app.add_route(route_selector, route_handler, True)

    def on_invoke_custom_event(self, handler: RouteQueryHandler[TState]):

        route_selector = create_route_selector("invokeCustomEvent")

        async def route_handler(context: TurnContext, state: TState):
            message_extension_query = MessageExtensionQuery.model_validate(context.activity.value)
            result = await handler(context, state, message_extension_query)
            response = Activity(type=ActivityTypes.invoke_response, value=InvokeResponse(
                status=200,
                body=result
            ))
            await context.send_activity(response)
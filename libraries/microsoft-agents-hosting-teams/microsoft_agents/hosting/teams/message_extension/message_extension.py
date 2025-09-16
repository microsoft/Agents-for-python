from mailbox import Message
from typing import Callable, Optional, TypeVar, Union, Awaitable

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteHandler,
    RouteSelector,
    TurnContext,
    TurnsState
)

from ..task_module import TaskModule
from .messaging_extension_action_response import MessagingExtensionActionResponse
from .messaging_extension_query import MessagingExtensionQuery
from .messaging_extension_response import MessagingExtensionResponse
from .messaging_extension_result import MessagingExtensionResult
from .messaging_extension_action import MessagingExtensionAction

RouteQueryHandler = TypeVar(
    "RouteQueryHandler",
    bound=Awaitable[[TurnContext, TState, MessagingExtensionQuery], MessagingExtensionResult]
)
SelectItemHandler = TypeVar(
    "SelectItemHandler",
    bound=Awaitable[[TurnContext, TState, item: Any], MessagingExtensionResult]
)
QueryLinkHandler = TypeVar(
    "QueryLinkHandler",
    bound=Awaitable[[TurnContext, TState, url: str], MessagingExtensionResult]
)
# robrandao: TODO -> JS typo
FetchTaskHandler = TypeVar(
    "FetchTaskHandler",
    bound=Awaitable[[TurnContext, TState], TaskModuleResponse]
)

SubmitActionHandler = TypeVar(
    "SubmitActionHandler",
    bound=Awaitable[[TurnContext, TState, data: Any], MessagingExtensionActionResponse]
)

MessagePreviewEditHandler = TypeVar(
    "MessagePreviewEditHandler",
    bound=Awaitable[[TurnContext, TState, activity: Activity], MessagingExtensionActionResponse]
)

MessagePreviewSendHandler = TypeVar(
    "MessagePreviewSendHandler",
    bound=Awaitable[[TurnContext, TState, activity: Activity], None]
)

ConfigurationSettingsHandler = TypeVar(
    "ConfigurationSettingsHandler",
    bound=Awaitable[[TurnContext, TState, settings: dict], None]
)

CardButtonClickedHandler = TypeVar(
    "CardButtonClickedHandler",
    bound=Awaitable[[TurnContext, TState, card_data: dict], None]
)

RouteHandlerArgument = TypeVar(
    "RouteHandlerArgument",
    bound=Union[MessagingExtensionQuery, str, dict, Activity, None, Any]
)

ResponseType = TypeVar(
    "ResponseType",
    bound=Union[MessagingExtensionResult, MessagingExtensionActionResponse, TaskModuleResponse]
)

class MessageExtension:

    def __init__(self):
        self._app = None

    def _base_route_selector(self, compose_extension_name: str) -> bool:
        async def selector(context: TurnContext, state: TurnsState) -> bool:
            return context.activity.type == ActivityTypes.invoke and
                context.activity.channel_id == MS_TEAMS and
                context.activity.name == f"composeExtension/{compose_extension_name}"
        return selector
    
    def _simple_invoke_response_middleware(self, handler: RouteHandler) -> RouteHandler:
        async def middleware(context: TurnContext, state: TurnsState):
            await handler(context, state, context.activity.value)
            await context.send_activity(InvokeResponse(value={status: 200}))
        return middleware
    
    def _base_invoke_response_middleware(
            self,
            handler: RouteHandler,
            extra_arg_func: Optional[Callable[[TurnContext], RouteHandlerArgument]] = None,
            format_response: Optional[Callable[[ResponseType], ResponseType]] = None
        ) -> RouteHandler:

        if not format_response:
            format_response = lambda res: res

        # by returning an Awaitable rather than awaiting inside,
        # we save time... TODO -> is this true?
        if extra_arg_func is None:
            def call_handler(context: TurnContext, state: TurnsState) -> Awaitable[ResponseType]:
                return handler(context, state)
        else:
            def call_handler(context: TurnContext, state: TurnsState) -> Awaitable[ResponseType]:
                extra_arg = extra_arg_func(context)
                return handler(context, state, extra_arg)
            
        async def middleware(context: TurnContext, state: TurnsState):
            response = format_response(await call_handler(context, state))
            invoke_response = Activity(
                type=ActivityTypes.invoke_response,
                value={
                    "status": 200,
                    "body": response
                }
            )
            await context.send_activity(invoke_response)
        return middleware
    
    def _messaging_invoke_response_middleware(
            self,
            handler: RouteHandler,
            extra_arg_func: Optional[Callable[[TurnContext], RouteHandlerArgument]],
        ) -> RouteHandler:
        def format_response(result: MessagingExtensionResult) -> MessagingExtensionResponse:
            return MessagingExtensionResponse(compose_extension=result)
        return self._base_invoke_response_middleware(handler, extra_arg_func, format_response)
    
    def _messaging_on_event(
            self,
            handler: RouteHandler,
            activity_name: str,
            extra_arg_func: Optional[Callable[[TurnContext], RouteHandlerArgument]],
        ) -> RouteHandler:
        route_selector = self._base_route_selector(activity_name)
        route_handler = self._messaging_invoke_response_middleware(handler, extra_arg_func)
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_query(self, handler: RouteQueryHandler) -> RouteQueryHandler:
        return self._messaging_on_event(
            handler, "query", lambda ctx: ctx.activity.value)
    
    def on_select_item(self, handler: SelectItemHandler) -> SelectItemHandler:
        return self._messaging_on_event(
            handler, "selectItem", lambda ctx: ctx.activity.value)
    
    def on_query_link(self, handler: QueryLinkHandler) -> QueryLinkHandler:
        return self._messaging_on_event(
            handler, "queryLink", lambda ctx: ctx.activity.value.get("url"))
    
    def on_anonymous_query_link(self, handler: QueryLinkHandler) -> QueryLinkHandler:
        return self._messaging_on_event(
            handler, "anonymousQueryLink", lambda ctx: ctx.activity.value.get("url"))
    
    def on_fetch_task(self, handler: FetchTaskHandler) -> FetchTaskHandler:
        route_selector = self._base_route_selector("fetchTask")
        route_handler = self._base_invoke_response_middleware(handler)
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_submit_action(self, handler: SubmitActionHandler) -> SubmitActionHandler:
        route_selector = self._base_route_selector("submitAction") # robrandao: TODO -> JS comment about TODO
        route_handler = self._base_invoke_response_middleware(
            handler, lambda ctx: ctx.activity.value)
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_message_preview_edit(self, handler: MessagePreviewEditHandler) -> MessagePreviewEditHandler:
        async def route_selector(context: TurnContext, state: TurnsState) -> bool:
            return context.activity.type == ActivityTypes.invoke and
                context.activity.channel_id == MS_TEAMS and
                context.activity.name == "composeExtension/submitAction" and
                context.activity.value and context.activity.value.get("botMessagePreviewAction") == "edit"
        route_handler = self._base_invoke_response_middleware(
            handler, lambda ctx: Activity(ctx.activity.value))
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_message_preview_send(self, handler: MessagePreviewSendHandler) -> MessagePreviewSendHandler:
        async def route_selector(context: TurnContext, state: TurnsState) -> bool:
            return context.activity.type == ActivityTypes.invoke and
                context.activity.channel_id == MS_TEAMS and
                context.activity.name == "composeExtension/submitAction" and
                context.activity.value and context.activity.value.get("botMessagePreviewAction") == "send"
        route_handler = self._base_invoke_response_middleware(
            handler, lambda ctx: MessageExtensionAction(ctx.activity.value),
            lambda res: None)
        return self._app.add_route(route_selector, route_handler, True)

    def on_configuration_query_setting_url(self, handler: ConfigurationSettingsHandler) -> ConfigurationSettingsHandler:
        route_selector = self._base_route_selector("querySettingUrl")
        route_handler = self._simple_invoke_response_middleware(handler)
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_configuration_setting(self, handler: ConfigurationSettingsHandler) -> ConfigurationSettingsHandler:
        route_selector = self._base_route_selector("setting")
        route_handler = self._simple_invoke_response_middleware(handler)
        return self._app.add_route(route_selector, route_handler, True)
    
    def on_card_button_clicked(self, handler: CardButtonClickedHandler) -> CardButtonClickedHandler:
        route_selector = self._base_route_selector("onCardButtonClicked")
        route_handler = self._simple_invoke_response_middleware(handler)
        return self._app.add_route(route_selector, route_handler, True)
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Generic, Optional, Callable

from microsoft_teams.api.models import (
    MessagingExtensionQuery,
    MessagingExtensionAction,
    AppBasedLinkQuery,
)

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import (
    StateT,
    CommandSelector,
    _RouteDecorator
)

from microsoft_agents.hosting.teams._utils import (
    _match_selector,
    _send_invoke_response
)

from .route_handlers import (
    FetchTaskHandler,
    QueryHandler,
    SubmitActionHandler,
    MessagePreviewEditHandler,
    MessagePreviewSendHandler,
    QueryHandler,
    SelectItemHandler,
    QueryLinkHandler,
    QueryUrlSettingHandler,
    ConfigureSettingsHandler,
    CardButtonClickedHandler
)

class MessageExtension(Generic[StateT]):
    """
    Route registration for Teams Message Extension (composeExtension) invoke activities.
    Access via TeamsAgentExtension.message_extension.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def query(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[QueryHandler[StateT]]:
        """Register a handler for composeExtension/query invokes."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/query"
            ):
                return False

            value = context.activity.value
            command_value: Optional[str] = None
            if isinstance(value, dict):
                command_value = value.get("commandId") or value.get("command_id")
            elif value is not None:
                command_value = getattr(value, "commandId", None) or getattr(
                    value, "command_id", None
                )

            return _match_selector(command_id, command_value)

        def __call(func: QueryHandler[StateT]) -> QueryHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                query = MessagingExtensionQuery.model_validate(
                    context.activity.value or {}
                )
                response = await func(teams_context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def select_item(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[SelectItemHandler[StateT]]:
        """Register a handler for composeExtension/selectItem invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/selectItem"
            )

        def __call(func: SelectItemHandler[StateT]) -> SelectItemHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                response = await func(teams_context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def submit_action(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[SubmitActionHandler[StateT]]:
        """Register a handler for composeExtension/submitAction invokes (not bot message preview)."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value
            if isinstance(value, dict):
                bot_message_preview_action = value.get("botMessagePreviewAction")
                resolved_command_id = value.get("commandId") or value.get("command_id")
            else:
                bot_message_preview_action = getattr(
                    value, "botMessagePreviewAction", None
                )
                resolved_command_id = getattr(value, "commandId", None) or getattr(
                    value, "command_id", None
                )
            if bot_message_preview_action:
                return False
            return _match_selector(command_id, resolved_command_id)

        def __call(func: SubmitActionHandler[StateT]) -> SubmitActionHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(teams_context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def message_preview_edit(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MessagePreviewEditHandler[StateT]]:
        """Register a handler for composeExtension/submitAction with botMessagePreviewAction == 'edit'."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value or {}
            if value.get("botMessagePreviewAction") != "edit":
                return False
            return _match_selector(command_id, value.get("commandId"))

        def __call(func: MessagePreviewEditHandler[StateT]) -> MessagePreviewEditHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(teams_context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def message_preview_send(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[MessagePreviewSendHandler[StateT]]:
        """Register a handler for composeExtension/submitAction with botMessagePreviewAction == 'send'."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value or {}
            if value.get("botMessagePreviewAction") != "send":
                return False
            return _match_selector(command_id, value.get("commandId"))

        def __call(func: MessagePreviewSendHandler[StateT]) -> MessagePreviewSendHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                # activity_preview: Activity | None = None
                # if action.bot_activity_preview:
                #     activity_preview = Activity.model_validate(action.bot_activity_preview[0])
                # activity_preview =
                # action.bot_activity_preview[0]
                response = await func(teams_context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def fetch_task(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[FetchTaskHandler[StateT]]:
        """Register a handler for composeExtension/fetchTask invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/fetchTask"
                and _match_selector(
                    command_id,
                    (context.activity.value or {}).get("commandId"),
                )
            )

        def __call(func: FetchTaskHandler[StateT]) -> FetchTaskHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def query_link(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[QueryLinkHandler[StateT]]:
        """Register a handler for composeExtension/queryLink invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/queryLink"
            )

        def __call(func: QueryLinkHandler[StateT]) -> QueryLinkHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                query = AppBasedLinkQuery.model_validate(context.activity.value or {})
                response = await func(teams_context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def anonymous_query_link(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[QueryLinkHandler[StateT]]:
        """Register a handler for composeExtension/anonymousQueryLink invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/anonymousQueryLink"
            )

        def __call(func: QueryLinkHandler[StateT]) -> QueryLinkHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                query = AppBasedLinkQuery.model_validate(context.activity.value or {})
                response = await func(teams_context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def query_setting_url(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[QueryUrlSettingHandler[StateT]]:
        """Register a handler for composeExtension/querySettingUrl invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/querySettingUrl"
            )

        def __call(func: QueryUrlSettingHandler[StateT]) -> QueryUrlSettingHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context)
                query = MessagingExtensionQuery.model_validate(
                    context.activity.value or {}
                )
                response = await func(teams_context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def setting(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ConfigureSettingsHandler[StateT]]:
        """Register a handler for composeExtension/setting invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/setting"
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                await func(context, state, context.activity.value)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    def card_button_clicked(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[CardButtonClickedHandler[StateT]]:
        """Register a handler for composeExtension/onCardButtonClicked invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/onCardButtonClicked"
            )

        def __call(func: CardButtonClickedHandler[StateT]) -> CardButtonClickedHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                await func(context, state, context.activity.value)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

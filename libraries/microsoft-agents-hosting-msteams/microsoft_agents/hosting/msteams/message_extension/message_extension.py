# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams Message Extension (composeExtension) invokes."""

from typing import Generic, Optional, Callable, overload

from microsoft_teams.api.models import AppBasedLinkQuery
from microsoft_teams.api.models.messaging_extension import (
    MessagingExtensionQuery,
    MessagingExtensionAction,
)

from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    StateT,
    CommandSelector,
    _RouteDecorator,
)

from microsoft_agents.hosting.msteams._utils import (
    _get_command_id,
    _match_selector,
    _send_invoke_response,
)

from .route_handlers import (
    FetchActionHandler,
    QueryHandler,
    SubmitActionHandler,
    MessagePreviewEditHandler,
    MessagePreviewSendHandler,
    SelectItemHandler,
    QueryLinkHandler,
    QueryUrlSettingHandler,
    CardButtonClickedHandler,
    SettingHandler,
)


def _extract_activity_preview(value: object) -> Activity:
    """Extract and deserialize the first botActivityPreview entry.

    :param value: The raw composeExtension/submitAction activity value.
    :return: The first activity preview parsed as an :class:`Activity`.
    :raises ValueError: If value is not a dict or no preview entries are present.
    :raises pydantic.ValidationError: If the preview cannot be deserialized.
    """
    if not isinstance(value, dict):
        raise ValueError(
            f"botActivityPreview: activity.value must be a dict, got {type(value).__name__}"
        )
    previews = value.get("botActivityPreview") or []
    if not previews:
        raise ValueError(
            "botActivityPreview: no preview activity found in activity.value"
        )
    return Activity.model_validate(previews[0])


class MessageExtension(Generic[StateT]):
    """Route registration for Teams Message Extension (composeExtension) invoke activities.

    Access via :attr:`TeamsAgentExtension.message_extensions`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def query(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[QueryHandler[StateT]]:
        """Register a handler for composeExtension/query invokes.

        :param command_id: Optional command identifier or regex to match a specific Teams command.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: A decorator that registers the handler and returns it.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/query"
            ):
                return False

            value = context.activity.value
            return _match_selector(command_id, _get_command_id(value))

        def __call(func: QueryHandler[StateT]) -> QueryHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

    @overload
    def select_item(
        self, handler: SelectItemHandler[StateT]
    ) -> SelectItemHandler[StateT]: ...

    @overload
    def select_item(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[SelectItemHandler[StateT]]: ...

    def select_item(
        self,
        handler: Optional[SelectItemHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> SelectItemHandler[StateT] | _RouteDecorator[SelectItemHandler[StateT]]:
        """Register a handler for composeExtension/selectItem invokes.

        :param handler: Optional handler receiving the context, state, and selected item payload.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/selectItem"
            )

        def __call(func: SelectItemHandler[StateT]) -> SelectItemHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

        if handler is not None:
            return __call(handler)
        return __call

    def submit_action(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[SubmitActionHandler[StateT]]:
        """Register a handler for composeExtension/submitAction invokes.

        Excludes submitAction invokes that carry a bot message preview action.

        :param command_id: Optional command identifier or regex to match a specific Teams command.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: A decorator that registers the handler and returns it.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value
            if isinstance(value, dict):
                bot_message_preview_action = value.get("botMessagePreviewAction")
            else:
                bot_message_preview_action = getattr(
                    value, "botMessagePreviewAction", None
                )
            if bot_message_preview_action:
                return False
            return _match_selector(command_id, _get_command_id(value))

        def __call(func: SubmitActionHandler[StateT]) -> SubmitActionHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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
        """Register a handler for composeExtension message preview edit invokes.

        :param command_id: Optional command identifier or regex to match a specific Teams command.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: A decorator that registers the handler and returns it.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value
            if not isinstance(value, dict):
                return False
            if value.get("botMessagePreviewAction") != "edit":
                return False
            return _match_selector(command_id, _get_command_id(value))

        def __call(
            func: MessagePreviewEditHandler[StateT],
        ) -> MessagePreviewEditHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                activity_preview = _extract_activity_preview(context.activity.value)
                response = await func(teams_context, state, activity_preview)
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
        """Register a handler for composeExtension message preview send invokes.

        :param command_id: Optional command identifier or regex to match a specific Teams command.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: A decorator that registers the handler and returns it.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value
            if not isinstance(value, dict):
                return False
            if value.get("botMessagePreviewAction") != "send":
                return False
            return _match_selector(command_id, _get_command_id(value))

        def __call(
            func: MessagePreviewSendHandler[StateT],
        ) -> MessagePreviewSendHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                activity_preview = _extract_activity_preview(context.activity.value)
                response = await func(teams_context, state, activity_preview)
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

    def fetch_action(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[FetchActionHandler[StateT]]:
        """Register a handler for composeExtension/fetchTask invokes.

        :param command_id: Optional command identifier or regex to match a specific Teams command.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: A decorator that registers the handler and returns it.
        """

        def __selector(context: TurnContext) -> bool:
            value = context.activity.value
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/fetchTask"
                and isinstance(value, dict)
                and _match_selector(command_id, _get_command_id(value))
            )

        def __call(func: FetchActionHandler[StateT]) -> FetchActionHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

    @overload
    def query_link(
        self, handler: QueryLinkHandler[StateT]
    ) -> QueryLinkHandler[StateT]: ...

    @overload
    def query_link(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[QueryLinkHandler[StateT]]: ...

    def query_link(
        self,
        handler: Optional[QueryLinkHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> QueryLinkHandler[StateT] | _RouteDecorator[QueryLinkHandler[StateT]]:
        """Register a handler for composeExtension/queryLink invokes.

        :param handler: Optional handler receiving the context, state, and app-based link query.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/queryLink"
            )

        def __call(func: QueryLinkHandler[StateT]) -> QueryLinkHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def anonymous_query_link(
        self, handler: QueryLinkHandler[StateT]
    ) -> QueryLinkHandler[StateT]: ...

    @overload
    def anonymous_query_link(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[QueryLinkHandler[StateT]]: ...

    def anonymous_query_link(
        self,
        handler: Optional[QueryLinkHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> QueryLinkHandler[StateT] | _RouteDecorator[QueryLinkHandler[StateT]]:
        """Register a handler for composeExtension/anonymousQueryLink invokes.

        :param handler: Optional handler receiving the context, state, and app-based link query.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/anonymousQueryLink"
            )

        def __call(func: QueryLinkHandler[StateT]) -> QueryLinkHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def query_setting_url(
        self, handler: QueryUrlSettingHandler[StateT]
    ) -> QueryUrlSettingHandler[StateT]: ...

    @overload
    def query_setting_url(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[QueryUrlSettingHandler[StateT]]: ...

    def query_setting_url(
        self,
        handler: Optional[QueryUrlSettingHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> (
        QueryUrlSettingHandler[StateT] | _RouteDecorator[QueryUrlSettingHandler[StateT]]
    ):
        """Register a handler for composeExtension/querySettingUrl invokes.

        :param handler: Optional handler receiving the context, state, and settings URL query.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/querySettingUrl"
            )

        def __call(
            func: QueryUrlSettingHandler[StateT],
        ) -> QueryUrlSettingHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
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

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def setting(self, handler: SettingHandler[StateT]) -> SettingHandler[StateT]: ...

    @overload
    def setting(
        self, *, auth_handlers: list[str] | None = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[SettingHandler[StateT]]: ...

    def setting(
        self,
        handler: SettingHandler[StateT] | None = None,
        *,
        auth_handlers: list[str] | None = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> SettingHandler[StateT] | _RouteDecorator[SettingHandler[StateT]]:
        """Register a handler for composeExtension/setting invokes.

        :param handler: Optional handler receiving the context, state, and settings query payload.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/setting"
            )

        def __call(func: SettingHandler[StateT]) -> SettingHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                query = MessagingExtensionQuery.model_validate(
                    context.activity.value or {}
                )
                res = await func(teams_context, state, query)
                await _send_invoke_response(context, res)

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

    @overload
    def card_button_clicked(
        self, handler: CardButtonClickedHandler[StateT]
    ) -> CardButtonClickedHandler[StateT]: ...

    @overload
    def card_button_clicked(
        self, *, auth_handlers: list[str] | None = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[CardButtonClickedHandler[StateT]]: ...

    def card_button_clicked(
        self,
        handler: CardButtonClickedHandler[StateT] | None = None,
        *,
        auth_handlers: list[str] | None = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> (
        CardButtonClickedHandler[StateT]
        | _RouteDecorator[CardButtonClickedHandler[StateT]]
    ):
        """Register a handler for composeExtension/onCardButtonClicked invokes.

        :param handler: Optional handler receiving the context, state, and card action payload.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority.
        :return: The registered handler when provided, otherwise a decorator that registers it.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/onCardButtonClicked"
            )

        def __call(
            func: CardButtonClickedHandler[StateT],
        ) -> CardButtonClickedHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
                teams_context = TeamsTurnContext(context, self._app)
                await func(teams_context, state, context.activity.value)
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

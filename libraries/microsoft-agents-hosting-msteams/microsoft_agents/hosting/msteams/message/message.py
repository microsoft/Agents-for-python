# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams message update and actionable message activities."""

from typing import Generic, Optional, overload

from microsoft_teams.api.models.o365 import O365ConnectorCardActionQuery

from microsoft_agents.activity import ActivityTypes, Channels
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.msteams.route_handlers import (
    TeamsRouteHandler,
    wrap_teams_route_handler,
)
from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.msteams._utils import (
    _get_channel_event_type,
    _send_invoke_response,
)

from .route_handlers import ExecuteActionHandler, ReadReceiptHandler


class Message(Generic[StateT]):
    """Route registration for Teams message update and actionable message activities.

    Access via :attr:`TeamsAgentExtension.messages`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def _create_basic_decorator(
        self,
        event_type: str,
        message_type: ActivityTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Build a route decorator for a Teams message channel event type.

        :param event_type: Teams channel event type to match.
        :param message_type: Activity type that must carry the channel event.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: A decorator that registers a Teams route handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity matches the configured message event."""
            return (
                context.activity.type == message_type
                and context.activity.channel_id == Channels.ms_teams
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: TeamsRouteHandler[StateT]) -> TeamsRouteHandler[StateT]:
            """Register the supplied Teams route handler."""
            self._app.add_route(
                __selector,
                wrap_teams_route_handler(func, self._app),
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    @overload
    def edit(self, handler: TeamsRouteHandler[StateT]) -> TeamsRouteHandler[StateT]: ...

    @overload
    def edit(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]: ...

    def edit(
        self,
        handler: Optional[TeamsRouteHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamsRouteHandler[StateT] | _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams editMessage events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """
        decorator = self._create_basic_decorator(
            "editMessage",
            ActivityTypes.message_update,
            auth_handlers=auth_handlers,
            rank=rank,
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def undelete(
        self, handler: TeamsRouteHandler[StateT]
    ) -> TeamsRouteHandler[StateT]: ...

    @overload
    def undelete(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]: ...

    def undelete(
        self,
        handler: Optional[TeamsRouteHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamsRouteHandler[StateT] | _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams undeleteMessage events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """
        decorator = self._create_basic_decorator(
            "undeleteMessage",
            ActivityTypes.message_update,
            auth_handlers=auth_handlers,
            rank=rank,
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def delete(
        self, handler: TeamsRouteHandler[StateT]
    ) -> TeamsRouteHandler[StateT]: ...

    @overload
    def delete(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]: ...

    def delete(
        self,
        handler: Optional[TeamsRouteHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> TeamsRouteHandler[StateT] | _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams softDeleteMessage events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """
        decorator = self._create_basic_decorator(
            "softDeleteMessage",
            ActivityTypes.message_delete,
            auth_handlers=auth_handlers,
            rank=rank,
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def read_receipt(
        self, handler: ReadReceiptHandler[StateT]
    ) -> ReadReceiptHandler[StateT]: ...

    @overload
    def read_receipt(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ReadReceiptHandler[StateT]]: ...

    def read_receipt(
        self,
        handler: Optional[ReadReceiptHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ReadReceiptHandler[StateT] | _RouteDecorator[ReadReceiptHandler[StateT]]:
        """Register a handler for Teams readReceipt events.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        :raises TypeError: If the incoming activity value is not a raw dict.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a Teams read receipt event."""
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.readReceipt"
            )

        def __call(func: ReadReceiptHandler[StateT]) -> ReadReceiptHandler[StateT]:
            """Register the supplied read receipt handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the raw read receipt payload and dispatch to the handler."""
                teams_context = TeamsTurnContext(context, self._app)
                value = context.activity.value
                if not isinstance(value, dict):
                    raise TypeError(
                        f"read_receipt: activity.value must be a dict, got {type(value).__name__}"
                    )
                await func(teams_context, state, value)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __call(handler)
        return __call

    @overload
    def execute_action(
        self, handler: ExecuteActionHandler[StateT]
    ) -> ExecuteActionHandler[StateT]: ...

    @overload
    def execute_action(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[ExecuteActionHandler[StateT]]: ...

    def execute_action(
        self,
        handler: Optional[ExecuteActionHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> ExecuteActionHandler[StateT] | _RouteDecorator[ExecuteActionHandler[StateT]]:
        """Register a handler for actionableMessage/executeAction invokes.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is an actionable message execute invoke."""
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "actionableMessage/executeAction"
            )

        def __call(func: ExecuteActionHandler[StateT]) -> ExecuteActionHandler[StateT]:
            """Register the supplied execute action handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the invoke payload and dispatch to the execute action handler."""
                teams_context = TeamsTurnContext(context, self._app)
                query = O365ConnectorCardActionQuery.model_validate(
                    context.activity.value or {}
                )
                await func(teams_context, state, query)
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

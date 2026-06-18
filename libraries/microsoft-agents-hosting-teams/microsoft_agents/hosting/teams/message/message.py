# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams message update and actionable message activities."""

from typing import Generic, Optional

from microsoft_teams.api.models.o365 import O365ConnectorCardActionQuery

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.teams.route_handlers import TeamsRouteHandler
from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.teams._utils import (
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
        """Build a route decorator for a Teams messageUpdate channel event type.

        :param event_type: The channel event type to match (e.g. ``"editMessage"``).
        :param message_type: The activity type to match.
        :param auth_handlers: Optional auth handler names to run before the route.
        :param rank: Route priority rank.
        :return: A decorator that registers the handler.
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == message_type
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __call(func: TeamsRouteHandler[StateT]) -> TeamsRouteHandler[StateT]:
            self._app.add_route(
                __selector,
                TeamsRouteHandler.wrap(func, self._app),
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def edit(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams editMessage events."""
        return self._create_basic_decorator(
            "editMessage",
            ActivityTypes.message_update,
            auth_handlers=auth_handlers,
            rank=rank,
        )

    def undelete(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams undeleteMessage events."""
        return self._create_basic_decorator(
            "undeleteMessage",
            ActivityTypes.message_update,
            auth_handlers=auth_handlers,
            rank=rank,
        )

    def soft_delete(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[TeamsRouteHandler[StateT]]:
        """Register a handler for Teams softDeleteMessage events."""
        return self._create_basic_decorator(
            "softDeleteMessage",
            ActivityTypes.message_delete,
            auth_handlers=auth_handlers,
            rank=rank,
        )

    def read_receipt(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ReadReceiptHandler[StateT]]:
        """Register a handler for Teams readReceipt events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.readReceipt"
            )

        def __call(func: ReadReceiptHandler[StateT]) -> ReadReceiptHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
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

        return __call

    def execute_action(
        self,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[ExecuteActionHandler[StateT]]:
        """Register a handler for actionableMessage/executeAction invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "actionableMessage/executeAction"
            )

        def __call(func: ExecuteActionHandler[StateT]) -> ExecuteActionHandler[StateT]:
            async def __handler(context: TurnContext, state: StateT) -> None:
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

        return __call

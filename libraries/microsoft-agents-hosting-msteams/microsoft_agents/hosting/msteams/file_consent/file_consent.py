# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Route registration helpers for Teams fileConsent/invoke activities."""

from typing import Generic, Optional, overload

from microsoft_teams.api.models import FileConsentCardResponse

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteRank,
    TurnContext,
)

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import (
    _RouteDecorator,
    StateT,
)
from microsoft_agents.hosting.msteams._utils import _send_invoke_response

from .route_handlers import FileConsentHandler


class FileConsent(Generic[StateT]):
    """Route registration for Teams file consent invoke activities.

    Access via :attr:`TeamsAgentExtension.file_consent`.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        """Initialise with the owning :class:`AgentApplication`.

        :param app: The application to register routes on.
        """
        self._app = app

    def _create_decorator(
        self,
        action: str,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> _RouteDecorator[FileConsentHandler[StateT]]:
        """Build a route decorator for a fileConsent/invoke action.

        :param action: File consent action value to match.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: A decorator that registers a file consent handler.
        """

        def __selector(context: TurnContext) -> bool:
            """Return True when the activity is a matching file consent invoke."""
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "fileConsent/invoke"
                and isinstance(context.activity.value, dict)
                and context.activity.value.get("action") == action
            )

        def __call(func: FileConsentHandler[StateT]) -> FileConsentHandler[StateT]:
            """Register the supplied file consent handler."""

            async def __handler(context: TurnContext, state: StateT) -> None:
                """Adapt the core turn context and dispatch to the file consent handler."""
                teams_context = TeamsTurnContext(context, self._app)
                file_consent = FileConsentCardResponse.model_validate(
                    context.activity.value or {}
                )
                await func(teams_context, state, file_consent)
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

    @overload
    def accept(
        self, handler: FileConsentHandler[StateT]
    ) -> FileConsentHandler[StateT]: ...

    @overload
    def accept(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[FileConsentHandler[StateT]]: ...

    def accept(
        self,
        handler: Optional[FileConsentHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> FileConsentHandler[StateT] | _RouteDecorator[FileConsentHandler[StateT]]:
        """Register a handler for accepted Teams file consent invokes.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """
        decorator = self._create_decorator(
            "accept", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

    @overload
    def decline(
        self, handler: FileConsentHandler[StateT]
    ) -> FileConsentHandler[StateT]: ...

    @overload
    def decline(
        self, *, auth_handlers: Optional[list[str]] = ..., rank: RouteRank = ...
    ) -> _RouteDecorator[FileConsentHandler[StateT]]: ...

    def decline(
        self,
        handler: Optional[FileConsentHandler[StateT]] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> FileConsentHandler[StateT] | _RouteDecorator[FileConsentHandler[StateT]]:
        """Register a handler for declined Teams file consent invokes.

        :param handler: Optional handler to register directly; omit for decorator use.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :param rank: Route priority used when multiple routes match.
        :return: The registered handler, or a decorator when used without a handler.
        """
        decorator = self._create_decorator(
            "decline", auth_handlers=auth_handlers, rank=rank
        )
        if handler is not None:
            return decorator(handler)
        return decorator

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, Generic, Protocol
from re import Pattern

from microsoft_agents.hosting.core.app import (
    AgentApplication,
    RouteHandler,
)
from microsoft_agents.hosting.core.app._type_defs import StateT

from .route_handlers import A2ARouteHandler, wrap_a2a_route_handler


class _AppRouteDecorator(Protocol[StateT]):
    """Protocol for a decorator returned by :class:`TeamsAgentExtension` route methods."""

    def __call__(self, func: A2ARouteHandler[StateT], /) -> RouteHandler[StateT]:
        """Register *func* as a Teams route handler.

        :param func: Teams-aware handler to register.
        :return: The wrapped core route handler.
        """
        ...


class A2AAgentExtension(Generic[StateT]):

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def _wrap_decorator(
        self, decorator: Callable[[RouteHandler[StateT]], RouteHandler[StateT]]
    ) -> Callable[[A2ARouteHandler[StateT]], RouteHandler[StateT]]:
        """Wrap a core route decorator so it accepts a :class:`TeamsRouteHandler`.

        The returned decorator converts the Teams handler via
        :func:`wrap_teams_route_handler` before passing it to *decorator*, keeping the
        Teams context upgrade transparent to callers.

        :param decorator: A core route decorator from :class:`AgentApplication`.
        :return: A decorator that accepts and registers a :class:`TeamsRouteHandler`.
        """

        def __call(func: A2ARouteHandler[StateT]) -> RouteHandler[StateT]:
            return decorator(wrap_a2a_route_handler(func, self._app))

        return __call

    def message(
        self,
        select: str | Pattern[str] | list[str | Pattern[str]],
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> _AppRouteDecorator[StateT]:
        """Register a handler for message activities matching *select*.

        :param select: A literal string, regex pattern, or list of either to match against
            the message text.
        :param auth_handlers: Optional list of auth handler names to run before the route.
        :return: A decorator that registers the handler and returns it.
        """
        return self._wrap_decorator(
            self._app.message(select, auth_handlers=auth_handlers, **kwargs)
        )

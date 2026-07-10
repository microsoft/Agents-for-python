# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Awaitable, Callable, Protocol

from .turn_context import TurnContext


class Middleware(Protocol):

    @abstractmethod
    async def on_turn(
        self, context: TurnContext, logic: Callable[[TurnContext], Awaitable]
    ):
        """
        Called for each turn of the conversation.

        :param context: The turn context.
        :param logic: The next middleware in the pipeline or the final logic to be executed.
        """
        pass


class MiddlewareSet(Middleware):
    """
    A set of `Middleware` plugins. The set itself is middleware so you can easily package up a set
    of middleware that can be composed into an agent with a single `agent.use(mySet)` call or even into
    another middleware set using `set.use(mySet)`.
    """

    def __init__(self):
        super().__init__()
        self._middleware: list[Middleware] = []

    def use(self, *middleware: Middleware):
        """
        Registers middleware plugin(s) with the agent or set.
        :param middleware : The middleware plugin(s) to register.
        :return: The `MiddlewareSet` instance to allow chaining of `use` calls.
        """
        for idx, mid in enumerate(middleware):
            if hasattr(mid, "on_turn") and callable(mid.on_turn):
                self._middleware.append(mid)
            else:
                raise TypeError(
                    'MiddlewareSet.use(): invalid middleware at index "%s" being added.'
                    % idx
                )
        return self

    async def _receive_activity_internal(
        self,
        context: TurnContext,
        callback: Callable[[TurnContext], Awaitable] | None,
        next_middleware_index: int = 0,
    ):
        if next_middleware_index == len(self._middleware):
            if callback is not None:
                return await callback(context)
            return None

        next_middleware = self._middleware[next_middleware_index]

        async def call_next_middleware(ctx: TurnContext):
            return await self._receive_activity_internal(
                ctx, callback, next_middleware_index + 1
            )

        return await next_middleware.on_turn(context, call_next_middleware)

    async def on_turn(
        self, context: TurnContext, logic: Callable[[TurnContext], Awaitable] | None
    ):
        """Handles an incoming activity by passing it through the middleware pipeline and then to the final logic.

        :param context: The turn context.
        :param logic: The final logic to be executed after the middleware pipeline.
        """
        return await self._receive_activity_internal(context, logic)

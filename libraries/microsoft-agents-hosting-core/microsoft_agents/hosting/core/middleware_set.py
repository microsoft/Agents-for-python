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
        pass


class MiddlewareSet(Middleware):
    """
    A set of `Middleware` plugins. The set itself is middleware so you can easily package up a set
    of middleware that can be composed into an agent with a single `agent.use(mySet)` call or even into
    another middleware set using `set.use(mySet)`.
    """

    def __init__(self):
        super(MiddlewareSet, self).__init__()
        self._middleware: list[Middleware] = []

    def use(self, *middleware: Middleware):
        """
        Registers middleware plugin(s) with the agent or set.
        :param middleware :
        :return:
        """
        for idx, mid in enumerate(middleware):
            if hasattr(mid, "on_turn") and callable(mid.on_turn):
                self._middleware.append(mid)
                return self
            raise TypeError(
                'MiddlewareSet.use(): invalid middleware at index "%s" being added.'
                % idx
            )

    async def receive_activity(self, context: TurnContext):
        await self.receive_activity_internal(context, None)

    async def on_turn(
        self, context: TurnContext, logic: Callable[[TurnContext], Awaitable]
    ):
        await self.receive_activity_internal(context, None)
        await logic()

    async def receive_activity_with_status(
        self, context: TurnContext, callback: Callable[[TurnContext], Awaitable]
    ):
        return await self.receive_activity_internal(context, callback)

    async def receive_activity_internal(
        self,
        context: TurnContext,
        callback: Callable[[TurnContext], Awaitable],
        next_middleware_index: int = 0,
    ):
        if next_middleware_index == len(self._middleware):
            if callback is not None:
                return await callback(context)
            return None
        next_middleware = self._middleware[next_middleware_index]

        async def call_next_middleware():
            return await self.receive_activity_internal(
                context, callback, next_middleware_index + 1
            )

        try:
            return await next_middleware.on_turn(context, call_next_middleware)
        except Exception as error:
            raise error

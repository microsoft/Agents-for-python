# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Awaitable, Protocol

from microsoft_agents.activity import (
    AdaptiveCardInvokeResponse,
    AdaptiveCardInvokeValue,
)

from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.app.state import TurnState

from .models import (
    AdaptiveCardSearchParams,
    AdaptiveCardSearchResult,
    Query,
)


class ActionExecuteHandler(Protocol):
    def __call__(
        self, context: TurnContext, state: TurnState, data: object, /
    ) -> Awaitable[AdaptiveCardInvokeResponse]: ...


class ActionExecuteValueHandler(Protocol):
    def __call__(
        self, context: TurnContext, state: TurnState, value: AdaptiveCardInvokeValue, /
    ) -> Awaitable[AdaptiveCardInvokeResponse]: ...


class ActionSubmitHandler(Protocol):
    def __call__(
        self, context: TurnContext, state: TurnState, data: object, /
    ) -> Awaitable[None]: ...


class SearchHandler(Protocol):
    def __call__(
        self,
        context: TurnContext,
        state: TurnState,
        query: Query[AdaptiveCardSearchParams],
        /,
    ) -> Awaitable[list[AdaptiveCardSearchResult]]: ...

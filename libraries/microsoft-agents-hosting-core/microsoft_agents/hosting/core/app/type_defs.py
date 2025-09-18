from typing import Callable, TypeVar, Awaitable, Protocol

from microsoft_agents.hosting.core import TurnContext, TurnState

StateT = TypeVar("StateT", bound=TurnState)
RouteSelector = Callable[[TurnContext], bool]

class RouteHandler(Protocol[StateT]):
    def __call__(self, context: TurnContext, state: StateT) -> Awaitable[None]:
        ...
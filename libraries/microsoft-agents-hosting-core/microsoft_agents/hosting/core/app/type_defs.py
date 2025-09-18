from typing import Callable, TypeVar, Awaitable, Protocol

from microsoft_agents.hosting.core import TurnContext, TurnState

RouteSelector = Callable[[TurnContext], bool]

StateT = TypeVar("StateT", bound=TurnState)
class RouteHandler(Protocol[StateT]):
    def __call__(self, context: TurnContext, state: StateT) -> Awaitable[None]:
        ...
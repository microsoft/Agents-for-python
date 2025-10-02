from __future__ import annotations

from typing import Optional, Protocol, TypeVar
from microsoft_agents.activity import AgentsModel
from microsoft_agents.hosting.core import TurnContext, TurnState

from strenum import StrEnum

StateT = TypeVar("StateT", bound=TurnState)


class CustomRouteHandler(Protocol(StateT)):
    async def __call__(
        self, context: TurnContext, state: StateT, event_data: CustomEventData
    ) -> CustomEventResult: ...


class CustomEventTypes(StrEnum):
    CUSTOM_EVENT = "customEvent"
    OTHER_CUSTOM_EVENT = "otherCustomEvent"


class CustomEventData(AgentsModel):
    user_id: Optional[str] = None
    field: Optional[str] = None

    @staticmethod
    def from_context(context) -> CustomEventData:
        return CustomEventData(
            user_id=context.activity.from_property.id,
            field=context.activity.channel_data.get("field"),
        )


class CustomEventResult(AgentsModel):
    user_id: Optional[str] = None
    field: Optional[str] = None

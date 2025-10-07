from __future__ import annotations

from typing import Optional, Protocol, TypeVar
from microsoft_agents.activity import AgentsModel
from microsoft_agents.hosting.core import TurnContext, TurnState

from strenum import StrEnum

StateT = TypeVar("StateT", bound=TurnState)


# this is defined as a class to allow for robust generic typing
class CustomRouteHandler(Protocol[StateT]):
    """A protocol for route handlers that accept custom event data."""

    async def __call__(
        self, context: TurnContext, state: StateT, data: CustomEventData
    ) -> Optional[CustomEventResult]: ...


class CustomEventTypes(StrEnum):
    """Custom event types used in the extension."""

    CUSTOM_EVENT = "customEvent"
    OTHER_CUSTOM_EVENT = "otherCustomEvent"


# inheriting from AgentsModel allows for easy serialization/deserialization
# using Pydantic features
class CustomEventData(AgentsModel):
    """Dummy data extracted from the activity for custom events."""

    user_id: Optional[str] = None
    field: Optional[str] = None

    @staticmethod
    def from_context(context) -> CustomEventData:
        return CustomEventData(
            user_id=context.activity.from_property.id,
            field=(
                context.activity.channel_data.get("field")
                if context.activity.channel_data
                else None
            ),
        )


class CustomEventResult(AgentsModel):
    """Dummy result returned by custom event handlers."""

    user_id: Optional[str] = None
    field: Optional[str] = None

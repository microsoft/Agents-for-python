from __future__ import annotations

from typing import Optional
from microsoft_agents.activity import AgentsModel

class CustomEventData(AgentsModel):
    user_id: Optional[str] = None
    field: Optional[str] = None

    @staticmethod
    def from_context(context) -> CustomEventData:
        return CustomEventData(
            user_id=context.activity.from_property.id,
            field=context.activity.channel_data.get("field")
        )
from typing import Literal, Optional

from microsoft_agents.activity import AgentsModel

class MeetingTabIconSurface(AgentsModel):
    surface: Literal["meetingTabIcon"] = "meetingTabIcon"
    tab_entity_id: Optional[str] = None
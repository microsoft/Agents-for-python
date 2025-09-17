from typing import Optional

from microsoft_agents.activity import AgentsModel

from ..activity_extensions.on_behalf_of import OnBehalfOf

class MeetingNotificationChannelData(AgentsModel):
    on_behalf_of: Optional[list[OnBehalfOf]] = None
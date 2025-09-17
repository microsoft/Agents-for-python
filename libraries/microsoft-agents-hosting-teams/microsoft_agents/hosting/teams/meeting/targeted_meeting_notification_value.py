from microsoft_agents.activity import AgentsModel

from .meeting_surface import MeetingSurface

class TargetedMeetingNotificationValue(AgentsModel):
    recipients: list[str]
    surfaces: list[MeetingSurface]
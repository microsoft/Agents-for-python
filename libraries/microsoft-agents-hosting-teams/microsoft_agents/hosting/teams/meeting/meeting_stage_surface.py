from typing import Literal

from microsoft_agents.activity import AgentsModel

class MeetingStageSurface(AgentsModel):
    surface: Literal["meetingStage"] = "meetingStage"
    content_type: Literal["task"] = "task"
    content: T
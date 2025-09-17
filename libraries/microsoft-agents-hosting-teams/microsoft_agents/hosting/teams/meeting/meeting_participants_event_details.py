from annotated_types import T
from microsoft_agents.activity import AgentsModel

from .teams_meeting_member import TeamsMeetingMember

class MeetingParticipantsEventDetails(AgentsModel):
    members: list[TeamsMeetingMember]
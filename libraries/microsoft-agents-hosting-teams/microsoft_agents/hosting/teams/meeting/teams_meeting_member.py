from microsoft_agents.activity import AgentsModel

from ..activity_extensions.teams_channel_account import TeamsChannelAccount
from .user_meeting_details import UserMeetingDetails

class TeamsMeetingMember(AgentsModel):
    user: TeamsChannelAccount
    meeting_details: UserMeetingDetails
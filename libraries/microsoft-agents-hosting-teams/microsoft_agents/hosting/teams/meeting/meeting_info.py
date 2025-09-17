from microsoft_agents.activity import ConversationAccount, AgentsModel
from ..meeting.meeting_details import MeetingDetails
from ..activity_extensions.teams_channel_account import TeamsChannelAccount

class MeetingInfo(AgentsModel):
    details: MeetingDetails
    conversation: ConversationAccount
    organizer: TeamsChannelAccount
from typing import Optional

from microsoft_agents.activity import AgentsModel, ConversationAccount
from microsoft_agents.hosting.core import TurnState

from .meeting import Meeting
from ..activity_extensions.teams_channel_account import TeamsChannelAccount

# robrandao: TODO -> generic
class TeamsMeetingParticipant(AgentsModel):
    user: Optional[TeamsChannelAccount] = None
    meeting: Optional[Meeting] = None
    conversation: Optional[ConversationAccount] = None
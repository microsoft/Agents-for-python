from pydantic import BaseModel
from typing import Optional


class TeamsMeetingParticipant(BaseModel):
    """Teams participant channel account detailing user Azure Active Directory and meeting participant details.

    :param user: Teams Channel Account information for this meeting participant
    :type user: Optional["TeamsChannelAccount"]
    :param meeting: Information specific to this participant in the specific meeting.
    :type meeting: Optional["MeetingParticipantInfo"]
    :param conversation: Conversation Account for the meeting.
    :type conversation: Optional["ConversationAccount"]
    """

    user: Optional["TeamsChannelAccount"]
    meeting: Optional["MeetingParticipantInfo"]
    conversation: Optional["ConversationAccount"]

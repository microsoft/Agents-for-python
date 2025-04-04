from pydantic import BaseModel
from typing import Optional


class MeetingParticipantInfo(BaseModel):
    """Information about a meeting participant.

    :param role: The role of the participant in the meeting.
    :type role: Optional[str]
    :param in_meeting: Indicates whether the participant is currently in the meeting.
    :type in_meeting: Optional[bool]
    """

    role: Optional[str]
    in_meeting: Optional[bool]

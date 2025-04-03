from pydantic import BaseModel
from typing import List


class MeetingParticipantsEventDetails(BaseModel):
    """Data about the meeting participants.

    :param members: The members involved in the meeting event.
    :type members: list[TeamsMeetingMember]
    """

    members: List["TeamsMeetingMember"]

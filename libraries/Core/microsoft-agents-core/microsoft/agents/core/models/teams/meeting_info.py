from pydantic import BaseModel
from typing import Optional

from .meeting_details import MeetingDetails


class MeetingInfo(BaseModel):
    """General information about a Teams meeting.

    :param details: The specific details of a Teams meeting.
    :type details: MeetingDetails
    :param conversation: The Conversation Account for the meeting.
    :type conversation: Optional[object]
    :param organizer: The meeting's organizer details.
    :type organizer: Optional[object]
    """

    details: Optional[MeetingDetails]
    conversation: Optional[object]
    organizer: Optional[object]

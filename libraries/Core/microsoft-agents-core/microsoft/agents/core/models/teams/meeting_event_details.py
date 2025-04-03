from pydantic import BaseModel
from typing import Optional


class MeetingEventDetails(BaseModel):
    """Base class for Teams meeting start and end events.

    :param id: The meeting's Id, encoded as a BASE64 string.
    :type id: str
    :param join_url: The URL used to join the meeting.
    :type join_url: str
    :param title: The title of the meeting.
    :type title: str
    :param meeting_type: The meeting's type.
    :type meeting_type: Optional[str]
    """

    id: str
    join_url: Optional[str]
    title: Optional[str]
    meeting_type: Optional[str]

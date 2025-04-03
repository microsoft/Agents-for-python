from pydantic import BaseModel
from typing import Optional


class MeetingEndEventDetails(BaseModel):
    """Specific details of a Teams meeting end event.

    :param id: The meeting's Id, encoded as a BASE64 string.
    :type id: str
    :param join_url: The URL used to join the meeting.
    :type join_url: str
    :param title: The title of the meeting.
    :type title: str
    :param end_time: Timestamp for meeting end, in UTC.
    :type end_time: Optional[str]
    """

    id: str
    join_url: Optional[str]
    title: Optional[str]
    end_time: Optional[str]

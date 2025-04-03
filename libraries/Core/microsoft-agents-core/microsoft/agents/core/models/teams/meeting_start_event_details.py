from pydantic import BaseModel
from typing import Optional


class MeetingStartEventDetails(BaseModel):
    """Specific details of a Teams meeting start event.

    :param id: The meeting's Id, encoded as a BASE64 string.
    :type id: str
    :param join_url: The URL used to join the meeting.
    :type join_url: str
    :param title: The title of the meeting.
    :type title: str
    :param start_time: Timestamp for meeting start, in UTC.
    :type start_time: Optional[str]
    """

    id: str
    join_url: Optional[str]
    title: Optional[str]
    start_time: Optional[str]

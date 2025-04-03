from pydantic import BaseModel
from typing import Optional


class MeetingDetails(BaseModel):
    """Specific details of a Teams meeting.

    :param id: The meeting's Id, encoded as a BASE64 string.
    :type id: str
    :param join_url: The URL used to join the meeting.
    :type join_url: str
    :param title: The title of the meeting.
    :type title: str
    :param ms_graph_resource_id: The MsGraphResourceId, used specifically for MS Graph API calls.
    :type ms_graph_resource_id: Optional[str]
    :param scheduled_start_time: The meeting's scheduled start time, in UTC.
    :type scheduled_start_time: Optional[str]
    :param scheduled_end_time: The meeting's scheduled end time, in UTC.
    :type scheduled_end_time: Optional[str]
    :param type: The meeting's type.
    :type type: Optional[str]
    """

    id: str
    join_url: Optional[str]
    title: Optional[str]
    ms_graph_resource_id: Optional[str]
    scheduled_start_time: Optional[str]
    scheduled_end_time: Optional[str]
    type: Optional[str]

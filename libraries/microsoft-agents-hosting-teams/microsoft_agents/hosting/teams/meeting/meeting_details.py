from typing import Optional

from .meeting_details_base import MeetingDetailsBase

class MeetingDetails(MeetingDetailsBase):
    ms_graph_resource_id: str
    scheduled_start_time: Optional[str] = None
    scheduled_end_time: Optional[str] = None
    type: str
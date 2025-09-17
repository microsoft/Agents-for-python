from datetime import datetime

from .meeting_event_details import MeetingEventDetails

class MeetingStartEventDetails(MeetingEventDetails):
    start_time: datetime
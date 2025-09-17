from datetime import datetime

from .meeting_event_details import MeetingEventDetails

class MeetingEndEventDetails(MeetingEventDetails):
    end_time: datetime
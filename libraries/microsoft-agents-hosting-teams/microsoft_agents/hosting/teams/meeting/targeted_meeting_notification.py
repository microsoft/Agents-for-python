from typing import Optional

from .meeting_notification_base import MeetingNotificationBase
from .meeting_notification_channel_data import MeetingNotificationChannelData
from .targeted_meeting_notification_value import TargetedMeetingNotificationValue

class TargetedMeetingNotification(MeetingNotificationBase<TargetedMeetingNotificationValue>):
    type: Literal["targetedMeetingNotification"] = "targetedMeetingNotification"
    channel_data: Optional[MeetingNotificationChannelData] = None
from pydantic import BaseModel
from .meeting_notification_base import MeetingNotificationBase


class MeetingNotification(MeetingNotificationBase):
    """Specifies Bot meeting notification including meeting notification value.

    :param value: Teams Bot meeting notification value.
    :type value: TargetedMeetingNotificationValue
    """

    value: "TargetedMeetingNotificationValue"

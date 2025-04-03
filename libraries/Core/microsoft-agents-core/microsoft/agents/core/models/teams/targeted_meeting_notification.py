from pydantic import BaseModel
from typing import List


class TargetedMeetingNotification(BaseModel):
    """Specifies Teams targeted meeting notification.

    :param value: The value of the TargetedMeetingNotification.
    :type value: TargetedMeetingNotificationValue
    :param channel_data: Teams Bot meeting notification channel data.
    :type channel_data: MeetingNotificationChannelData
    """

    value: "TargetedMeetingNotificationValue"
    channel_data: "MeetingNotificationChannelData"

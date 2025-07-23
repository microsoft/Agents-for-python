# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .meeting_notification import MeetingNotification
from .targeted_meeting_notification_value import TargetedMeetingNotificationValue
from .meeting_notification_channel_data import MeetingNotificationChannelData


class TargetedMeetingNotification(MeetingNotification):
    """Specifies Teams targeted meeting notification.

    :param value: The value of the TargetedMeetingNotification.
    :type value: TargetedMeetingNotificationValue
    :param channel_data: Teams Bot meeting notification channel data.
    :type channel_data: MeetingNotificationChannelData
    """

    value: TargetedMeetingNotificationValue = None
    channel_data: MeetingNotificationChannelData = None

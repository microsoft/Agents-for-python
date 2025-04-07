# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .meeting_notification_base import MeetingNotificationBase
from .targeted_meeting_notification_value import TargetedMeetingNotificationValue


class MeetingNotification(MeetingNotificationBase):
    """Specifies Bot meeting notification including meeting notification value.

    :param value: Teams Bot meeting notification value.
    :type value: TargetedMeetingNotificationValue
    """

    value: TargetedMeetingNotificationValue = None

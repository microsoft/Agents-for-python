# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .meeting_notification_recipient_failure_info import (
    MeetingNotificationRecipientFailureInfo,
)


class MeetingNotificationResponse(AgentsModel):
    """Specifies Bot meeting notification response.

    Contains list of MeetingNotificationRecipientFailureInfo.

    :param recipients_failure_info: The list of MeetingNotificationRecipientFailureInfo.
    :type recipients_failure_info: list[MeetingNotificationRecipientFailureInfo]
    """

    recipients_failure_info: list[MeetingNotificationRecipientFailureInfo] = None

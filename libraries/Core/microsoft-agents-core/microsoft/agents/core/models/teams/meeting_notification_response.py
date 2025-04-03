from pydantic import BaseModel
from typing import List


class MeetingNotificationRecipientFailureInfo(BaseModel):
    recipient_mri: str
    error_code: str
    failure_reason: str


class MeetingNotificationResponse(BaseModel):
    """Specifies Bot meeting notification response.

    Contains list of MeetingNotificationRecipientFailureInfo.

    :param recipients_failure_info: The list of MeetingNotificationRecipientFailureInfo.
    :type recipients_failure_info: list[MeetingNotificationRecipientFailureInfo]
    """

    recipients_failure_info: List[MeetingNotificationRecipientFailureInfo]

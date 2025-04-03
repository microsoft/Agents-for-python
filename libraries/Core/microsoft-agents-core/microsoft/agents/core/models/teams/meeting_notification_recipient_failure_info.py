from pydantic import BaseModel


class MeetingNotificationRecipientFailureInfo(BaseModel):
    """Information regarding failure to notify a recipient of a meeting notification.

    :param recipient_mri: The MRI for a recipient meeting notification failure.
    :type recipient_mri: str
    :param error_code: The error code for a meeting notification.
    :type error_code: str
    :param failure_reason: The reason why a participant meeting notification failed.
    :type failure_reason: str
    """

    recipient_mri: str
    error_code: str
    failure_reason: str

from pydantic import BaseModel
from typing import List


class TargetedMeetingNotificationValue(BaseModel):
    """Specifies the value for targeted meeting notifications.

    :param recipients: List of recipient MRIs for the notification.
    :type recipients: List[str]
    :param message: The message content of the notification.
    :type message: str
    """

    recipients: List[str]
    message: str

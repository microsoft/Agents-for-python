from pydantic import BaseModel
from typing import Optional


class NotificationInfo(BaseModel):
    """Specifies if a notification is to be sent for the mentions.

    :param alert: True if notification is to be sent to the user, false otherwise.
    :type alert: bool
    :param alert_in_meeting: True if notification is to be sent in a meeting context.
    :type alert_in_meeting: Optional[bool]
    :param external_resource_url: URL for external resources related to the notification.
    :type external_resource_url: Optional[str]
    """

    alert: bool
    alert_in_meeting: Optional[bool]
    external_resource_url: Optional[str]

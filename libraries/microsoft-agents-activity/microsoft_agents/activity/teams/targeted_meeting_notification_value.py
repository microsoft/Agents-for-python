# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .surface import Surface


class TargetedMeetingNotificationValue(AgentsModel):
    """Specifies the value for targeted meeting notifications.

    :param recipients: List of recipient MRIs for the notification.
    :type recipients: list[str]
    :param message: The message content of the notification.
    :type message: str
    """

    recipients: list[str] = None
    surfaces: list[Surface] = None

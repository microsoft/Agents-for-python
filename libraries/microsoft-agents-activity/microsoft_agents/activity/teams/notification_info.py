# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class NotificationInfo(AgentsModel):
    """Specifies if a notification is to be sent for the mentions.

    :param alert: True if notification is to be sent to the user, false otherwise.
    :type alert: bool
    :param alert_in_meeting: True if notification is to be sent in a meeting context.
    :type alert_in_meeting: bool | None
    :param external_resource_url: URL for external resources related to the notification.
    :type external_resource_url: str | None
    """

    alert: bool = None
    alert_in_meeting: bool | None = None
    external_resource_url: str | None = None

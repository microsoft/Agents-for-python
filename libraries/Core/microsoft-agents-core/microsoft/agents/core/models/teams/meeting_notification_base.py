# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class MeetingNotificationBase(BaseModel):
    """Specifies Bot meeting notification base including channel data and type.

    :param type: Type of Bot meeting notification.
    :type type: str
    """

    type: str = None

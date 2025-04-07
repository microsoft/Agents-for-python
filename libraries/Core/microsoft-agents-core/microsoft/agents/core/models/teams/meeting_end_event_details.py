# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import Optional


class MeetingEndEventDetails(BaseModel):
    """Specific details of a Teams meeting end event.

    :param end_time: Timestamp for meeting end, in UTC.
    :type end_time: str
    """

    end_time: str = None

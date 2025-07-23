# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional


class MeetingEndEventDetails(AgentsModel):
    """Specific details of a Teams meeting end event.

    :param end_time: Timestamp for meeting end, in UTC.
    :type end_time: str
    """

    end_time: str = None

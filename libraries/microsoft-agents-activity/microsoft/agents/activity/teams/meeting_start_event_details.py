# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional


class MeetingStartEventDetails(AgentsModel):
    """Specific details of a Teams meeting start event.

    :param start_time: Timestamp for meeting start, in UTC.
    :type start_time: str
    """

    start_time: str = None

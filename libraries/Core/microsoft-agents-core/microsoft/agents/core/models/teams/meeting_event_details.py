# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional


class MeetingEventDetails(AgentsModel):
    """Base class for Teams meeting start and end events.

    :param meeting_type: The meeting's type.
    :type meeting_type: str
    """

    meeting_type: str = None

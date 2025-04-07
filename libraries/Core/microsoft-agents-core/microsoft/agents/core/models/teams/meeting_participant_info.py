# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import Optional


class MeetingParticipantInfo(BaseModel):
    """Information about a meeting participant.

    :param role: The role of the participant in the meeting.
    :type role: str
    :param in_meeting: Indicates whether the participant is currently in the meeting.
    :type in_meeting: bool
    """

    role: str = None
    in_meeting: bool = None

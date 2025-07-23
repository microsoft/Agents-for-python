# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List
from .teams_meeting_member import TeamsMeetingMember


class MeetingParticipantsEventDetails(AgentsModel):
    """Data about the meeting participants.

    :param members: The members involved in the meeting event.
    :type members: list[TeamsMeetingMember]
    """

    members: List[TeamsMeetingMember] = None

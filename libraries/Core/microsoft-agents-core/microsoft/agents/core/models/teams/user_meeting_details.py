# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class UserMeetingDetails(AgentsModel):
    """Specific details of a user in a Teams meeting.

    :param role: Role of the participant in the current meeting.
    :type role: str
    :param in_meeting: True, if the participant is in the meeting.
    :type in_meeting: bool
    """

    role: str = None
    in_meeting: bool = None

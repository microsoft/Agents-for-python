# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .teams_channel_account import TeamsChannelAccount
from .user_meeting_details import UserMeetingDetails


class TeamsMeetingMember(AgentsModel):
    """Data about the meeting participants.

    :param user: The channel user data.
    :type user: TeamsChannelAccount
    :param meeting: The user meeting details.
    :type meeting: UserMeetingDetails
    """

    user: TeamsChannelAccount = None
    meeting: UserMeetingDetails = None

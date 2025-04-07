# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from .teams_channel_account import TeamsChannelAccount
from .user_meeting_details import UserMeetingDetails


class TeamsMeetingMember(BaseModel):
    """Data about the meeting participants.

    :param user: The channel user data.
    :type user: TeamsChannelAccount
    :param meeting: The user meeting details.
    :type meeting: UserMeetingDetails
    """

    user: TeamsChannelAccount = None
    meeting: UserMeetingDetails = None

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .meeting_details import MeetingDetails
from .teams_channel_account import TeamsChannelAccount
from ..conversation_account import ConversationAccount


class MeetingInfo(AgentsModel):
    """General information about a Teams meeting.

    :param details: The specific details of a Teams meeting.
    :type details: MeetingDetails
    :param conversation: The Conversation Account for the meeting.
    :type conversation: ConversationAccount
    :param organizer: The meeting's organizer details.
    :type organizer: TeamsChannelAccount
    """

    details: MeetingDetails = None
    conversation: ConversationAccount = None
    organizer: TeamsChannelAccount = None

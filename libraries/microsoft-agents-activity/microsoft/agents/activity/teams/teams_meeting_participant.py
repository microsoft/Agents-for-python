# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .teams_channel_account import TeamsChannelAccount
from .meeting_participant_info import MeetingParticipantInfo
from ..conversation_account import ConversationAccount


class TeamsMeetingParticipant(AgentsModel):
    """Teams participant channel account detailing user Azure Active Directory and meeting participant details.

    :param user: Teams Channel Account information for this meeting participant
    :type user: TeamsChannelAccount
    :param meeting: Information specific to this participant in the specific meeting.
    :type meeting: MeetingParticipantInfo
    :param conversation: Conversation Account for the meeting.
    :type conversation: ConversationAccount
    """

    user: TeamsChannelAccount = None
    meeting: MeetingParticipantInfo = None
    conversation: ConversationAccount = None

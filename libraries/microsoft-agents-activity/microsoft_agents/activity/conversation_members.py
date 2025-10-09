# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .channel_account import ChannelAccount
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationMembers(AgentsModel):
    """Conversation and its members.

    :param id: Conversation ID
    :type id: str
    :param members: List of members in this conversation
    :type members: list[~microsoft_agents.activity.ChannelAccount]
    """

    id: NonEmptyString = None
    members: list[ChannelAccount] = None

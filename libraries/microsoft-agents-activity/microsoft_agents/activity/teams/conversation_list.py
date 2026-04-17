# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .channel_info import ChannelInfo


class ConversationList(AgentsModel):
    """List of channels under a team.

    :param conversations: List of ChannelInfo objects.
    :type conversations: list[ChannelInfo]
    """

    conversations: list[ChannelInfo]

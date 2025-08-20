# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .channel_info import ChannelInfo


class TeamsChannelDataSettings(AgentsModel):
    """Represents the settings information for a Teams channel data.

    :param selected_channel: Information about the selected Teams channel.
    :type selected_channel: ChannelInfo
    """

    selected_channel: ChannelInfo = None

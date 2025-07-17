# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List
from .teams_channel_account import TeamsChannelAccount


class TeamsPagedMembersResult(AgentsModel):
    """Page of members for Teams.

    :param continuation_token: Paging token
    :type continuation_token: str
    :param members: The Teams Channel Accounts.
    :type members: list[TeamsChannelAccount]
    """

    continuation_token: str = None
    members: List[TeamsChannelAccount] = None

from pydantic import BaseModel
from typing import List


class TeamsPagedMembersResult(BaseModel):
    """Page of members for Teams.

    :param continuation_token: Paging token
    :type continuation_token: str
    :param members: The Teams Channel Accounts.
    :type members: list[TeamsChannelAccount]
    """

    continuation_token: str
    members: List["TeamsChannelAccount"]

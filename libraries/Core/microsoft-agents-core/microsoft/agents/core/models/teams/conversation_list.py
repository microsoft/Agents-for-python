from pydantic import BaseModel
from typing import List


class ChannelInfo(BaseModel):
    id: str
    name: str
    type: str


class ConversationList(BaseModel):
    """List of channels under a team.

    :param conversations: List of ChannelInfo objects.
    :type conversations: List[ChannelInfo]
    """

    conversations: List[ChannelInfo]

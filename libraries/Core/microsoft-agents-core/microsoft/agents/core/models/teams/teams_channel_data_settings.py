from pydantic import BaseModel
from typing import Optional


class TeamsChannelDataSettings(BaseModel):
    """Represents the settings information for a Teams channel data.

    :param selected_channel: Information about the selected Teams channel.
    :type selected_channel: Optional["ChannelInfo"]
    """

    selected_channel: Optional["ChannelInfo"]

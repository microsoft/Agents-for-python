from typing import Optional

from microsoft_agents.activity import AgentsModel

from .channel_info import ChannelInfo

class TeamsChannelDataSettings(AgentsModel):
    selected_channel: Optional[ChannelInfo] = None
    # robrandao: TODO -> properties
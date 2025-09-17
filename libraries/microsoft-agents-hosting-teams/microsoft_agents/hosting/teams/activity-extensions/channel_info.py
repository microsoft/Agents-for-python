from token import OP
from typing import Optional

from microsoft_agents.activity import AgentsModel

from .enums import ChannelTypes

class ChannelInfo(AgentsModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[ChannelTypes] = None
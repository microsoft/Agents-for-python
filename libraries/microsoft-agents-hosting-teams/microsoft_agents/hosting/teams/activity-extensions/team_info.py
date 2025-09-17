from token import OP
from typing import Optional

from microsoft_agents.activity import AgentsModel

class TeamInfo(AgentsModel):
    id: Optional[str] = None
    name: Optional[str] = None
    aad_group_id: Optional[str] = None
    tenant_id: Optional[str] = None
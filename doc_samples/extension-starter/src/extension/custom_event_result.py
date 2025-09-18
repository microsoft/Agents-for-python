from typing import Optional
from microsoft_agents.activity import AgentsModel

class CustomEventResult(AgentsModel):
    user_id: Optional[str] = None
    field: Optional[str] = None
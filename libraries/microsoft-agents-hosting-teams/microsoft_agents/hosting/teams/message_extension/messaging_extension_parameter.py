from typing import Optional, ANy
from microsoft_agents.activity import AgentsModel

class MessagingExtensionParameter(AgentsModel):
    name: Optional[str] = None
    value: Optional[Any] = None # robrandao: TODO -> any lowercase?
from typing import Optional, Any

from microsoft_agents.activity import AgentsModel

class MessageActionsPayloadAttachment(AgentsModel):
    id: Optional[str] = None
    content_type: Optional[str] = None
    content_url: Optional[str] = None
    content: Optional[Any] = None
    name: Optional[str] = None
    thumbnail_url: Optional[str] = None
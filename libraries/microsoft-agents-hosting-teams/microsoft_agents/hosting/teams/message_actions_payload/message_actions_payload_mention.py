from typing import Optional

from microsoft_agents.activity import AgentsModel

from .message_actions_payload_from import MessageActionsPayloadFrom

class MessageActionsPayloadMention(AgentsModel):
    id: Optional[int] = None
    mention_text: Optional[str] = None
    mentioned: Optional[MessageActionsPayloadFrom] = None
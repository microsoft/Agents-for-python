from typing import Optional

from microsoft_agents.activity import AgentsModel

from .message_actions_payload_app import MessageActionsPayloadApp
from .message_actions_payload_conversation import MessageActionsPayloadConversation
from .message_actions_payload_user import MessageActionsPayloadUser

class MessageActionsPayloadFrom(AgentsModel):
    user: Optional[MessageActionsPayloadUser] = None
    application: Optional[MessageActionsPayloadApp] = None
    conversation: Optional[MessageActionsPayloadConversation] = None
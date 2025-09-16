from token import OP
from typing import TypeVar, Union, Optional
from venv import create

from microsoft_agents.activity import AgentsModel

from .message_actions_payload_attachments import MessageActionsPayloadAttachments
from .message_actions_payload_body import MessageActionsPayloadBody
from .message_actions_payload_from import MessageActionsPayloadFrom
from .message_actions_payload_mention import MessageActionsPayloadMention
from .message_actions_payload_reaction import MessageActionsPayloadReaction

MessageType = TypeVar("MessageType", Literal["message"])
Importance = TypeVar("Importance", Literal["normal", "high", "urgent"])

class MessageActionsPayload(AgentsModel):
    id: Optional[str] = None
    reply_to_id: Optional[str] = None
    message_type: Optional[MessageType] = None
    created_data_time: Optional[str] = None
    last_modified_date_time: Optional[str] = None
    deleted: Optional[bool] = None
    subject: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[Importance] = None
    locale: Optional[str] = None
    link_to_message: Optional[str] = None
    from_property: Optional[MessageActionsPayloadFrom] = None
    body: Optional[MessageActionsPayloadBody] = None
    attachmentLayout: Optional[str] = None
    attachments: Optional[list[MessageActionsPayloadAttachments]] = None
    mentions: Optional[list[MessageActionsPayloadMention]] = None
    reactions: Optional[list[MessageActionsPayloadReaction]] = None
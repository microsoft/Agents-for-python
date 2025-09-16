from typing import Optional, Union, Literal, TypeVar

from microsoft_agents.activity import AgentsModel

ContentType = TypeVar("ContentType", Literal["text", "html"])

class MessageActionsPayloadBody(AgentsModel):
    content_type: Optional[ContentType] = None
    content: Optional[str] = None
    text_content: Optional[str] = None
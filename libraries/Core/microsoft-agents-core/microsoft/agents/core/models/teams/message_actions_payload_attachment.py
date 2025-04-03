from pydantic import BaseModel
from typing import Any, Optional


class MessageActionsPayloadAttachment(BaseModel):
    """Represents the attachment in a message.

    :param id: The id of the attachment.
    :type id: str
    :param content_type: The type of the attachment.
    :type content_type: str
    :param content_url: The url of the attachment, in case of an external link.
    :type content_url: str
    :param content: The content of the attachment, in case of a code snippet, email, or file.
    :type content: Any
    :param name: The plaintext display name of the attachment.
    :type name: str
    :param thumbnail_url: The url of a thumbnail image that might be embedded in the attachment, in case of a card.
    :type thumbnail_url: Optional[str]
    """

    id: str
    content_type: str
    content_url: str
    content: Any
    name: str
    thumbnail_url: Optional[str]

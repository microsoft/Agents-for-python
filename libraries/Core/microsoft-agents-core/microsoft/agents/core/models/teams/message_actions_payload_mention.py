from pydantic import BaseModel
from typing import Optional


class MessageActionsPayloadMention(BaseModel):
    """Represents the entity that was mentioned in the message.

    :param id: The id of the mentioned entity.
    :type id: int
    :param mention_text: The plaintext display name of the mentioned entity.
    :type mention_text: str
    :param mentioned: Provides more details on the mentioned entity.
    :type mentioned: Optional["MessageActionsPayloadFrom"]
    """

    id: int
    mention_text: str
    mentioned: Optional["MessageActionsPayloadFrom"]

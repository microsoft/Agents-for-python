from pydantic import BaseModel
from typing import Optional


class MessageActionsPayloadReaction(BaseModel):
    """Represents the reaction of a user to a message.

    :param reaction_type: The type of reaction given to the message. Possible values include: 'like', 'heart', 'laugh', 'surprised', 'sad', 'angry'
    :type reaction_type: str
    :param created_date_time: Timestamp of when the user reacted to the message.
    :type created_date_time: str
    :param user: The user with which the reaction is associated.
    :type user: Optional["MessageActionsPayloadFrom"]
    """

    reaction_type: str
    created_date_time: str
    user: Optional["MessageActionsPayloadFrom"]

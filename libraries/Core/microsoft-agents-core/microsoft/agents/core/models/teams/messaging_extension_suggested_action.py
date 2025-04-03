from pydantic import BaseModel
from typing import List


class MessagingExtensionSuggestedAction(BaseModel):
    """Messaging extension suggested actions.

    :param actions: List of suggested actions.
    :type actions: List["CardAction"]
    """

    actions: List["CardAction"]

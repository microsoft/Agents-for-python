# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional

from .message_actions_payload_from import MessageActionsPayloadFrom


class MessageActionsPayloadMention(AgentsModel):
    """Represents the entity that was mentioned in the message.

    :param id: The id of the mentioned entity.
    :type id: Optional[int]
    :param mention_text: The plaintext display name of the mentioned entity.
    :type mention_text: Optional[str]
    :param mentioned: Provides more details on the mentioned entity.
    :type mentioned: Optional["MessageActionsPayloadFrom"]
    """

    id: Optional[int]
    mention_text: Optional[str]
    mentioned: Optional[MessageActionsPayloadFrom]

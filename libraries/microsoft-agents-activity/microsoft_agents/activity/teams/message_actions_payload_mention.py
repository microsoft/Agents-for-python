# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .message_actions_payload_from import MessageActionsPayloadFrom


class MessageActionsPayloadMention(AgentsModel):
    """Represents the entity that was mentioned in the message.

    :param id: The id of the mentioned entity.
    :type id: int | None
    :param mention_text: The plaintext display name of the mentioned entity.
    :type mention_text: str | None
    :param mentioned: Provides more details on the mentioned entity.
    :type mentioned: MessageActionsPayloadFrom | None
    """

    id: int | None
    mention_text: str | None
    mentioned: MessageActionsPayloadFrom | None

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .message_actions_payload_from import MessageActionsPayloadFrom


class MessageActionsPayloadReaction(AgentsModel):
    """Represents the reaction of a user to a message.

    :param reaction_type: The type of reaction given to the message. Possible values include: 'like', 'heart', 'laugh', 'surprised', 'sad', 'angry'
    :type reaction_type: str | None
    :param created_date_time: Timestamp of when the user reacted to the message.
    :type created_date_time: str | None
    :param user: The user with which the reaction is associated.
    :type user: MessageActionsPayloadFrom | None
    """

    reaction_type: str | None
    created_date_time: str | None
    user: MessageActionsPayloadFrom | None

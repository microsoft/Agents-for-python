# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class MessageActionsPayloadConversation(AgentsModel):
    """Represents a team or channel entity.

    :param conversation_identity_type: The type of conversation, whether a team or channel.
    :type conversation_identity_type: str
    :param id: The id of the team or channel.
    :type id: str
    :param display_name: The plaintext display name of the team or channel entity.
    :type display_name: str
    """

    conversation_identity_type: str = None
    id: str = None
    display_name: str = None

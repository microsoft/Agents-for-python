# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .conversation_members import ConversationMembers
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationsResult(AgentsModel):
    """Conversations result.

    :param continuation_token: Paging token
    :type continuation_token: str
    :param conversations: List of conversations
    :type conversations:
     list[~microsoft_agents.activity.ConversationMembers]
    """

    continuation_token: NonEmptyString = None
    conversations: list[ConversationMembers] = None

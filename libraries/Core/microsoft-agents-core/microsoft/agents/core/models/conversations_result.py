from .conversation_members import ConversationMembers
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationsResult(AgentsModel):
    """Conversations result.

    :param continuation_token: Paging token
    :type continuation_token: str
    :param conversations: List of conversations
    :type conversations:
     list[~microsoft.agents.protocols.models.ConversationMembers]
    """

    continuation_token: NonEmptyString = None
    conversations: list[ConversationMembers] = None

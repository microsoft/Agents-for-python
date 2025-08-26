from .channel_account import ChannelAccount
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationMembers(AgentsModel):
    """Conversation and its members.

    :param id: Conversation ID
    :type id: str
    :param members: List of members in this conversation
    :type members: list[~microsoft.agents.protocols.models.ChannelAccount]
    """

    id: NonEmptyString = None
    members: list[ChannelAccount] = None

from .channel_account import ChannelAccount
from ._agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class Mention(AgentsModel):
    """Mention information (entity type: "mention").

    :param mentioned: The mentioned user
    :type mentioned: ~microsoft.agents.protocols.models.ChannelAccount
    :param text: Sub Text which represents the mention (can be null or empty)
    :type text: str
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    mentioned: ChannelAccount = None
    text: NonEmptyString = None
    type: NonEmptyString = None

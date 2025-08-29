from typing import Literal

from ..channel_account import ChannelAccount
from .._type_aliases import NonEmptyString
from .entity_types import EntityTypes, AtEntityTypes
from .entity import Entity

class Mention(Entity):
    """Mention information (entity type: "mention").

    :param mentioned: The mentioned user
    :type mentioned: ~microsoft_agents.activity.ChannelAccount
    :param text: Sub Text which represents the mention (can be null or empty)
    :type text: str
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    type: Literal[EntityTypes.MENTION] = EntityTypes.MENTION
    at_type: Literal[AtEntityTypes.MENTION] = AtEntityTypes.MENTION

    mentioned: ChannelAccount = None
    text: str = None

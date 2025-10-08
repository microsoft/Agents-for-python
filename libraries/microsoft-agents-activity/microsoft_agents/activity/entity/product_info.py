from .entity import Entity
from .entity_types import EntityTypes

class ProductInfo(Entity):
    """Product information (entity type: "productInfo").

    :param mentioned: The mentioned user
    :type mentioned: ~microsoft_agents.activity.ChannelAccount
    :param text: Sub Text which represents the mention (can be null or empty)
    :type text: str
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    type: str = EntityTypes.PRODUCT_INFO
    id: str = None
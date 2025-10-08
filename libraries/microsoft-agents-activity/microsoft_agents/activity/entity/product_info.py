from .entity import Entity
from .entity_types import EntityTypes


class ProductInfo(Entity):
    """Product information (entity type: "productInfo").

    :param type: The type of the entity, always "productInfo".
    :type type: str
    :param id: The unique identifier for the product.
    :type id: str
    """

    type: str = EntityTypes.PRODUCT_INFO
    id: str = None

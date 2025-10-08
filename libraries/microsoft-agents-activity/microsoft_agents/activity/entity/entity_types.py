from strenum import StrEnum

class EntityTypes(StrEnum):
    """Enumeration of entity types."""

    GEO_COORDINATES = "GeoCoordinates"
    PLACE = "Place"
    THING = "Thing"
    PRODUCT_INFO = "ProductInfo"
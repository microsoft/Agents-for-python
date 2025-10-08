from strenum import StrEnum


class EntityTypes(StrEnum):
    """Well-known enumeration of entity types."""

    GEO_COORDINATES = "geoCoordinates"
    PLACE = "place"
    THING = "thing"
    PRODUCT_INFO = "productInfo"

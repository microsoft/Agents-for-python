from enum import Enum

class AtEntityTypes(str, Enum):
    GEO_COORDINATES = "at_geo_coordinates"
    MENTION = "at_mention"
    PLACE = "at_place"
    THING = "at_thing"
    SENSITIVITY_USAGE_INFO = "at_sensitivity_usage_info"
    AI_ENTITY = "at_ai_entity"

# common entities that can be referenced without IRI
class EntityTypes(str, Enum):
    GEO_COORDINATES = "geo_coordinates"
    MENTION = "mention"
    PLACE = "place"
    THING = "thing"
    SENSITIVITY_USAGE_INFO = "sensitivity_usage_info"
    AI_ENTITY = "ai_entity"

    IRI_MAPPING = {
        GEO_COORDINATES: "https://schema.org/GeoCoordinates",
        MENTION: "https://botframework.com/schema/mention",
        PLACE: "https://schema.org/Place",
        THING: "https://schema.org/Thing",
    }

    @classmethod
    def iri(cls, name):
        return cls.IRI_MAPPING.get(name)
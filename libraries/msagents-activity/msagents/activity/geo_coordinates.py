from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class GeoCoordinates(AgentsModel):
    """GeoCoordinates (entity type: "https://schema.org/GeoCoordinates").

    :param elevation: Elevation of the location [WGS
     84](https://en.wikipedia.org/wiki/World_Geodetic_System)
    :type elevation: float
    :param latitude: Latitude of the location [WGS
     84](https://en.wikipedia.org/wiki/World_Geodetic_System)
    :type latitude: float
    :param longitude: Longitude of the location [WGS
     84](https://en.wikipedia.org/wiki/World_Geodetic_System)
    :type longitude: float
    :param type: The type of the thing
    :type type: str
    :param name: The name of the thing
    :type name: str
    """

    elevation: float = None
    latitude: float = None
    longitude: float = None
    type: NonEmptyString = None
    name: NonEmptyString = None

from typing import Literal

from .._type_aliases import NonEmptyString
from ..agents_model import AgentsModel
from .entity import Entity
from .entity_types import EntityTypes, AtEntityTypes



class Place(Entity):
    """Place (entity type: "https://schema.org/Place").

    :param address: Address of the place (may be `string` or complex object of
     type `PostalAddress`)
    :type address: object
    :param geo: Geo coordinates of the place (may be complex object of type
     `GeoCoordinates` or `GeoShape`)
    :type geo: object
    :param has_map: Map to the place (may be `string` (URL) or complex object
     of type `Map`)
    :type has_map: object
    :param type: The type of the thing
    :type type: str
    :param name: The name of the thing
    :type name: str
    """

    type: Literal[EntityTypes.PLACE] = EntityTypes.PLACE
    at_type: Literal[AtEntityTypes.PLACE] = AtEntityTypes.PLACE

    address: object = None
    geo: object = None
    has_map: object = None
    name: NonEmptyString = None

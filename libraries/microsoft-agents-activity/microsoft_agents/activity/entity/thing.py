from typing import Literal

from .._type_aliases import NonEmptyString
from .entity_types import EntityTypes, AtEntityTypes
from .entity import Entity

class Thing(Entity):
    """Thing (entity type: "https://schema.org/Thing").

    :param type: The type of the thing
    :type type: str
    :param name: The name of the thing
    :type name: str
    """
    type: Literal[EntityTypes.THING] = EntityTypes.THING
    at_type: Literal[AtEntityTypes.THING] = AtEntityTypes.THING

    name: NonEmptyString = None

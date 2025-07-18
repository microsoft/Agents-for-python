from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class Thing(AgentsModel):
    """Thing (entity type: "https://schema.org/Thing").

    :param type: The type of the thing
    :type type: str
    :param name: The name of the thing
    :type name: str
    """

    type: NonEmptyString = None
    name: NonEmptyString = None

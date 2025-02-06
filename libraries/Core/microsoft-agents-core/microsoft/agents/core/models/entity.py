from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class Entity(AgentsModel):
    """Metadata object pertaining to an activity.

    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    class Config:
        extra = "allow"

    type: NonEmptyString

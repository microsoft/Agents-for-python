from typing import Any
from .agents_model import AgentsModel, ConfigDict
from ._type_aliases import NonEmptyString


class Entity(AgentsModel):
    """Metadata object pertaining to an activity.

    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    model_config = ConfigDict(extra="allow")

    type: NonEmptyString

    @property
    def additional_properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra

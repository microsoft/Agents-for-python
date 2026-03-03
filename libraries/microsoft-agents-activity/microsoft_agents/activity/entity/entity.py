# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from pydantic import model_serializer, model_validator
from pydantic.alias_generators import to_camel, to_snake

from ..agents_model import AgentsModel, ConfigDict


class Entity(AgentsModel):
    """Metadata object pertaining to an activity.

    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    model_config = ConfigDict(extra="allow", alias_generator=to_camel, validate_by_name=True, validate_by_alias=True)

    type: str

    @property
    def additional_properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra
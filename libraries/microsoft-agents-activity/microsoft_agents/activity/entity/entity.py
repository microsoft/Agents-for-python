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

    model_config = ConfigDict(extra="allow")

    type: str

    @property
    def additional_properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra

    @model_validator(mode="before")
    @classmethod
    def to_snake_for_all(cls, data):
        ret = {to_snake(k): v for k, v in data.items()}
        return ret

    @model_serializer(mode="plain")
    def to_camel_for_all(self, config):
        if config.by_alias:
            new_data = {}
            for k, v in self:
                new_data[to_camel(k)] = v
            return new_data
        return {k: v for k, v in self}

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Self

from pydantic import (
    model_serializer,
    model_validator,
    SerializationInfo,
    ModelWrapValidatorHandler,
    SerializerFunctionWrapHandler,
)
from pydantic.alias_generators import to_camel, to_snake

from ..agents_model import AgentsModel, ConfigDict
from ._schema_mixin import validate_schema_model, serialize_schema_model


def _to_camel_exclude_at(k: str) -> str:
    """Helper function to convert keys to camelCase while preserving keys that start with '@'."""
    if k.startswith("@"):
        return k  # preserve keys starting with '@'
    return to_camel(k)


class Entity(AgentsModel):
    """Metadata object pertaining to an activity.

    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    model_config = ConfigDict(
        extra="allow",
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )

    type: str

    @property
    def additional_properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra

    @model_validator(mode="wrap")
    @classmethod
    def _validate_model(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        """Custom validator to handle both camelCase and snake_case keys, as well as @type, @context, and @id."""

        if isinstance(data, dict):
            new_data = {to_snake(k): v for k, v in data.items()}
            return validate_schema_model(new_data, handler)
        return validate_schema_model(data, handler)

    @model_serializer(mode="wrap")
    def _serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, object]:
        """Custom serializer to convert keys to camelCase and include @type, @context, and @id as needed.

        Forces the inclusion of the 'type' field in the serialized output, as it is a required field for Entity.
        """

        data = serialize_schema_model(self, handler, info)
        new_data: dict

        if info.by_alias:
            new_data = {_to_camel_exclude_at(k): v for k, v in data.items()}
        else:
            new_data = {k: v for k, v in data.items()}

        new_data["type"] = self.type  # ensure type is always included

        return new_data

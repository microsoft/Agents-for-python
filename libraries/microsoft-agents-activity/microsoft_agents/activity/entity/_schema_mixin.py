# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any
from pydantic import (
    model_serializer,
    model_validator,
    ModelWrapValidatorHandler,
    SerializerFunctionWrapHandler,
    SerializationInfo,
    BaseModel,
)


def _deserialize_at_field(
    data: dict[str, Any], model: BaseModel, model_field_name: str, input_field_name: str
) -> None:
    """Deserialize a single @-prefixed field from the input data into the model if it exists.

    :param data: The input data dictionary containing potential @-prefixed fields.
    :param model: The Pydantic model instance to populate with deserialized data.
    :param model_field_name: The name of the field in the model to populate.
    :param input_field_name: The name of the field in the input data to read from.
    """


def validate_schema_model(data: Any, handler: ModelWrapValidatorHandler):
    """Custom validator to handle the aliases @type, @context, and @id if defined in the destination type."""
    model = handler(data)
    if isinstance(data, dict):
        allows_extra = model.model_config.get("extra") == "allow"
        for model_field, input_field in [
            ("at_type", "@type"),
            ("at_context", "@context"),
            ("at_id", "@id"),
        ]:
            if input_field in data and (hasattr(model, model_field) or allows_extra):
                setattr(model, model_field, data[input_field])
    return model


def _serialize_at_field(
    model: BaseModel,
    serialized: dict[str, Any],
    model_field_name: str,
    output_field_name: str,
) -> None:
    """Serialize a non-None schema field using its @-prefixed name."""
    field = type(model).model_fields.get(model_field_name)
    if field is None:
        return

    alias = field.serialization_alias or field.alias or model_field_name
    serialized.pop(alias, None)

    value = getattr(model, model_field_name)
    if value is not None:
        serialized[output_field_name] = value


def serialize_schema_model(
    self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
) -> dict[str, Any]:
    """Custom serializer to convert keys to force inclusion of @type, @context, and @id if defined."""
    serialized = handler(self)
    if info.by_alias:
        for model_field, out_field in [
            ("at_type", "@type"),
            ("at_context", "@context"),
            ("at_id", "@id"),
        ]:
            _serialize_at_field(self, serialized, model_field, out_field)
    return serialized


class _SchemaMixin(BaseModel):
    """Mixin class to force inclusion of @property fields when serializing."""

    @model_validator(mode="wrap")
    @classmethod
    def _validate_model(cls, data: Any, handler: ModelWrapValidatorHandler):
        return validate_schema_model(data, handler)

    @model_serializer(mode="wrap")
    def _serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        return serialize_schema_model(self, handler, info)

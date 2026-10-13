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


def validate_schema_model(
    data: Any,
    handler: ModelWrapValidatorHandler,
    model_type: type[BaseModel],
):
    """Custom validator to handle the aliases @type, @context, and @id if defined in the destination type."""
    if isinstance(data, dict):
        normalized_data = dict(data)
        extra_schema_fields = {}
        allows_extra = model_type.model_config.get("extra") == "allow"

        for model_field, input_field in [
            ("at_type", "@type"),
            ("at_context", "@context"),
            ("at_id", "@id"),
        ]:
            if input_field not in data:
                continue

            field = model_type.model_fields.get(model_field)
            if field is not None:
                normalized_data.pop(input_field, None)
                normalized_data[model_field] = data[input_field]
            elif allows_extra:
                extra_schema_fields[model_field] = data[input_field]

        model = handler(normalized_data)
        for model_field, value in extra_schema_fields.items():
            setattr(model, model_field, value)
        return model

    model = handler(data)
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
        return validate_schema_model(data, handler, cls)

    @model_serializer(mode="wrap")
    def _serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        return serialize_schema_model(self, handler, info)
